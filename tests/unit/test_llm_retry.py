"""
LLM retry tests.

What this is:
- Unit tests for stage-2 LLM retry behavior.

What it does:
- Verifies retryable failures are retried.
- Verifies non-retryable failures are not retried.

Why this is done this way:
- Model retry logic is now part of the stage-2 stability contract and must be
  verified without requiring real model traffic.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.infrastructure.tools.failure_recovery import reset_circuit_breakers
from app.infrastructure.llm.client import LLMCallError, call_llm, get_llm_client, get_llm_settings


class LlmRetryTests(unittest.TestCase):
    def setUp(self) -> None:
        get_llm_settings.cache_clear()
        get_llm_client.cache_clear()

    def tearDown(self) -> None:
        get_llm_settings.cache_clear()
        get_llm_client.cache_clear()
        reset_circuit_breakers()

    def test_call_llm_retries_retryable_error(self) -> None:
        fake_response = type(
            "ChatResponseLike",
            (),
            {"choices": [type("ChoiceLike", (), {"message": type("MessageLike", (), {"content": "ok"})()})()]},
        )()

        retryable = LLMCallError("temporary", details={"retryable": "true"})
        with patch("app.infrastructure.llm.client.get_llm_settings") as mock_settings, patch(
            "app.infrastructure.llm.client.get_llm_client"
        ) as mock_client, patch(
            "app.infrastructure.llm.client.is_llm_retry_enabled",
            return_value=True,
        ), patch(
            "app.infrastructure.llm.client.get_llm_retry_attempts",
            return_value=2,
        ), patch(
            "app.infrastructure.llm.client.get_llm_retry_backoff_ms",
            return_value=0,
        ):
            mock_settings.return_value = type(
                "SettingsLike",
                (),
                {"provider": "openai", "model": "gpt-4o-mini", "api_key": "k", "base_url": None},
            )()
            mock_client.return_value.chat.completions.create.side_effect = [retryable, fake_response]

            result = call_llm("hello", trace_id="trace_test")

        self.assertEqual(result, "ok")

    def test_call_llm_does_not_retry_non_retryable_error(self) -> None:
        non_retryable = LLMCallError("invalid", details={"retryable": "false"})
        with patch("app.infrastructure.llm.client.get_llm_settings") as mock_settings, patch(
            "app.infrastructure.llm.client.get_llm_client"
        ) as mock_client, patch(
            "app.infrastructure.llm.client.is_llm_retry_enabled",
            return_value=True,
        ), patch(
            "app.infrastructure.llm.client.get_llm_retry_attempts",
            return_value=3,
        ), patch(
            "app.infrastructure.llm.client.get_llm_retry_backoff_ms",
            return_value=0,
        ):
            mock_settings.return_value = type(
                "SettingsLike",
                (),
                {"provider": "openai", "model": "gpt-4o-mini", "api_key": "k", "base_url": None},
            )()
            mock_client.return_value.chat.completions.create.side_effect = non_retryable

            with self.assertRaises(LLMCallError):
                call_llm("hello", trace_id="trace_test")

    def test_call_llm_opens_circuit_after_retryable_failures(self) -> None:
        retryable = LLMCallError("temporary", details={"retryable": "true"})
        with patch("app.infrastructure.llm.client.get_llm_settings") as mock_settings, patch(
            "app.infrastructure.llm.client.get_llm_client"
        ) as mock_client, patch(
            "app.infrastructure.llm.client.is_llm_retry_enabled",
            return_value=False,
        ), patch(
            "app.infrastructure.llm.client.is_llm_circuit_enabled",
            return_value=True,
        ), patch(
            "app.infrastructure.llm.client.get_llm_circuit_failure_threshold",
            return_value=1,
        ), patch(
            "app.infrastructure.llm.client.get_llm_circuit_recovery_seconds",
            return_value=30,
        ):
            mock_settings.return_value = type(
                "SettingsLike",
                (),
                {"provider": "openai", "model": "gpt-4o-mini", "api_key": "k", "base_url": None},
            )()
            mock_client.return_value.chat.completions.create.side_effect = retryable

            with self.assertRaises(LLMCallError):
                call_llm("hello", trace_id="trace_test")

            with self.assertRaises(LLMCallError) as second_error:
                call_llm("hello", trace_id="trace_test")

        self.assertEqual(second_error.exception.code, "llm_circuit_open")
