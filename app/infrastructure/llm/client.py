"""
LLM client module.

What this is:
- The unified model access layer for the current Agent runtime.

What it does:
- Loads provider configuration.
- Builds an OpenAI-compatible client.
- Exposes a stable `call_llm` entrypoint.
- Supports image multimodal input blocks when image assets are available.
- Applies retry, circuit-breaker, alerting, and optional degradation strategy.

Why this is done this way:
- Upper layers should only care about prompts, assets, and results instead of
  SDK details.
- Recovery, degradation, and observability need one stable place to avoid
  policy drift across CLI, API, and workflow code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    RateLimitError,
)

from app.application.services.config_service import RuntimeConfigService
from app.config import (
    get_llm_circuit_failure_threshold,
    get_llm_circuit_recovery_seconds,
    get_llm_retry_attempts,
    get_llm_retry_backoff_ms,
    is_llm_circuit_enabled,
    is_llm_retry_enabled,
)
from app.domain.errors import ModelError
from app.domain.models import InputAsset
from app.infrastructure.logger import get_logger
from app.infrastructure.tools.failure_recovery import emit_recovery_alert, get_circuit_breaker
from app.infrastructure.tools.retry_policy import execute_with_retry

load_dotenv()

logger = get_logger("infrastructure.llm.client")


class LLMCallError(ModelError):
    """
    What this is:
    - The stable model-layer error exposed to upper layers.

    What it does:
    - Wraps SDK and provider failures into a repository-level domain error.

    Why this is done this way:
    - API handlers and workflow nodes should not depend on third-party SDK
      exception shapes.
    """

    def __init__(self, message: str, trace_id: str | None = None, details: dict[str, str] | None = None) -> None:
        super().__init__(message, trace_id=trace_id, details=details)
        self.code = "llm_call_error"


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    model: str
    api_key: str
    base_url: str | None = None


PROVIDER_DEFAULTS = {
    "openai": {
        "model": "gpt-4o-mini",
        "base_url": None,
        "api_key_env": "OPENAI_API_KEY",
    },
    "dashscope": {
        "model": "qwen-plus",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
    },
    "doubao": {
        "model": "your-doubao-endpoint-id",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key_env": "ARK_API_KEY",
    },
    "custom": {
        "model": "your-model-name",
        "base_url": None,
        "api_key_env": "LLM_API_KEY",
    },
    "mock": {
        "model": "mock-model",
        "base_url": None,
        "api_key_env": "LLM_API_KEY",
    },
}


def sanitize_text(text: str) -> str:
    return text.encode("utf-8", errors="replace").decode("utf-8").strip()


def _get_provider_defaults(provider: str) -> dict[str, str | None]:
    return PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["custom"])


def _build_missing_key_message(provider: str) -> str:
    return (
        f"未检测到可用的 API Key。当前 Provider 为 `{provider}`。"
        "请在 .env 中配置 `LLM_API_KEY`，或配置当前 Provider 对应的专用 Key。"
    )


def _build_error_message(prefix: str, provider: str, model: str, error: Exception) -> str:
    return f"{prefix} 当前模型：`{provider}` / `{model}`。原始信息：{sanitize_text(str(error))}"


@lru_cache(maxsize=1)
def get_llm_settings() -> LLMSettings:
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    defaults = _get_provider_defaults(provider)

    api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv(str(defaults["api_key_env"]))
        or os.getenv("OPENAI_API_KEY")
        or ""
    )
    if provider != "mock" and not api_key:
        raise LLMCallError(_build_missing_key_message(provider))

    settings = LLMSettings(
        provider=provider,
        model=os.getenv("LLM_MODEL", str(defaults["model"])).strip(),
        api_key=api_key,
        base_url=(os.getenv("LLM_BASE_URL") or defaults["base_url"] or "").strip() or None,
    )
    logger.info(
        "已加载模型配置 provider=%s model=%s base_url=%s",
        settings.provider,
        settings.model,
        settings.base_url or "default",
    )
    return settings


@lru_cache(maxsize=1)
def get_llm_client() -> OpenAI:
    settings = get_llm_settings()
    client_kwargs = {"api_key": settings.api_key}
    if settings.base_url:
        client_kwargs["base_url"] = settings.base_url
    return OpenAI(**client_kwargs)


def _build_data_url(asset: InputAsset) -> str | None:
    mime_type = asset.get("mime_type")
    data_base64 = asset.get("data_base64")
    if not mime_type or not data_base64 or not mime_type.startswith("image/"):
        return None
    return f"data:{mime_type};base64,{data_base64}"


def _extract_multimodal_image_parts(input_assets: list[InputAsset] | None) -> list[dict[str, object]]:
    if not input_assets:
        return []

    content_parts: list[dict[str, object]] = []
    for asset in input_assets:
        if asset["kind"] != "image":
            continue
        if asset.get("url"):
            content_parts.append({"type": "image_url", "image_url": {"url": asset["url"]}})
            continue
        data_url = _build_data_url(asset)
        if data_url:
            content_parts.append({"type": "image_url", "image_url": {"url": data_url}})
    return content_parts


def _build_message_content(prompt: str, input_assets: list[InputAsset] | None) -> str | list[dict[str, object]]:
    image_parts = _extract_multimodal_image_parts(input_assets)
    if not image_parts:
        return prompt
    return [{"type": "text", "text": prompt}, *image_parts]


def _build_mock_response(cleaned_prompt: str, input_assets: list[InputAsset] | None, *, degraded: bool) -> str:
    has_image_assets = any(asset["kind"] == "image" for asset in (input_assets or []))
    prefix = "这是一个降级 mock " if degraded else "这是一个本地 mock "
    if "仲裁阶段" in cleaned_prompt:
        return f"{prefix}仲裁代理：建议保留双方共同认可的关键点，并在最终答案中补充风险与限制说明。"
    if "辩论阶段" in cleaned_prompt:
        if any(keyword in cleaned_prompt for keyword in {"支持方", "强项", "保留", "有效路径"}):
            return f"{prefix}支持方代理：当前规划覆盖了主要任务目标，最终答案应优先给出直接结论和关键依据。"
        return f"{prefix}质疑方代理：当前规划仍需强调限制条件、失败风险或潜在遗漏，避免结论过度乐观。"
    if "批评阶段" in cleaned_prompt:
        return f"{prefix}批评代理：当前结果基本完整，但如果涉及工具失败或明显限制，需要在答案中明确说明。"
    if "规划阶段" in cleaned_prompt:
        if has_image_assets:
            return f"{prefix}规划结果：先读取图片输入，再结合上下文给出分析。"
        return f"{prefix}规划结果：先理解任务，再结合上下文生成答案。"
    if has_image_assets:
        return f"{prefix}最终答案，用于验证真实图片入口和多模态消息拼装是否正常。"
    return f"{prefix}最终答案，用于验证 Agent 底座流程是否正常。"


def _get_recovery_config() -> dict[str, object]:
    return RuntimeConfigService().get_effective_recovery_config()


def call_llm(prompt: str, input_assets: list[InputAsset] | None = None, trace_id: str | None = None) -> str:
    settings = get_llm_settings()
    cleaned_prompt = sanitize_text(prompt)
    message_content = _build_message_content(cleaned_prompt, input_assets)

    logger.info(
        "开始调用模型 provider=%s model=%s trace_id=%s",
        settings.provider,
        settings.model,
        trace_id or "none",
    )
    logger.debug("发送给模型的 prompt：\n%s", cleaned_prompt)

    if settings.provider == "mock":
        return _build_mock_response(cleaned_prompt, input_assets, degraded=False)

    recovery_config = _get_recovery_config()
    llm_degrade_to_mock = bool(recovery_config["llm_degrade_to_mock"])

    breaker = None
    if is_llm_circuit_enabled():
        breaker = get_circuit_breaker(
            f"llm:{settings.provider}:{settings.model}",
            failure_threshold=get_llm_circuit_failure_threshold(),
            recovery_seconds=get_llm_circuit_recovery_seconds(),
        )
        if not breaker.allow_request():
            if llm_degrade_to_mock:
                emit_recovery_alert(
                    trace_id=trace_id or "none",
                    source_type="llm",
                    source_name=f"{settings.provider}:{settings.model}",
                    severity="warning",
                    event_code="llm_degraded_to_mock",
                    message="模型熔断开启后已降级到 mock 响应。",
                    payload={"provider": settings.provider, "model": settings.model},
                )
                return _build_mock_response(cleaned_prompt, input_assets, degraded=True)

            emit_recovery_alert(
                trace_id=trace_id or "none",
                source_type="llm",
                source_name=f"{settings.provider}:{settings.model}",
                severity="warning",
                event_code="llm_circuit_open_fast_fail",
                message="模型熔断已开启，本次请求进入快速失败。",
                payload={"provider": settings.provider, "model": settings.model},
            )
            degraded_error = LLMCallError(
                f"模型熔断已开启，暂时拒绝调用。当前模型：`{settings.provider}` / `{settings.model}`。",
                trace_id=trace_id,
                details={"retryable": "false", "degraded": "true", "degrade_mode": "fast_fail"},
            )
            degraded_error.code = "llm_circuit_open"
            raise degraded_error

    client = get_llm_client()

    def _invoke():
        try:
            return client.chat.completions.create(
                model=settings.model,
                messages=[{"role": "user", "content": message_content}],
            )
        except RateLimitError as error:
            raise LLMCallError(
                _build_error_message("模型调用触发 429，通常表示额度不足、未开通计费或限流。", settings.provider, settings.model, error),
                trace_id=trace_id,
                details={"retryable": "true"},
            ) from error
        except AuthenticationError as error:
            raise LLMCallError(
                _build_error_message("模型认证失败。请检查 API Key、Base URL 和模型配置。", settings.provider, settings.model, error),
                trace_id=trace_id,
                details={"retryable": "false"},
            ) from error
        except BadRequestError as error:
            raise LLMCallError(
                _build_error_message("模型请求参数错误。请检查模型名、输入内容和多模态请求格式。", settings.provider, settings.model, error),
                trace_id=trace_id,
                details={"retryable": "false"},
            ) from error
        except APIConnectionError as error:
            raise LLMCallError(
                _build_error_message("模型网络连接失败。请检查当前网络和代理配置。", settings.provider, settings.model, error),
                trace_id=trace_id,
                details={"retryable": "true"},
            ) from error
        except APIStatusError as error:
            retryable = error.status_code >= 500
            raise LLMCallError(
                _build_error_message(f"模型服务返回 HTTP {error.status_code}。", settings.provider, settings.model, error),
                trace_id=trace_id,
                details={"retryable": "true" if retryable else "false"},
            ) from error
        except LLMCallError:
            raise
        except Exception as error:
            logger.exception("模型调用发生未预期异常")
            raise LLMCallError(
                _build_error_message("模型调用发生未预期异常。", settings.provider, settings.model, error),
                trace_id=trace_id,
                details={"retryable": "false"},
            ) from error

    def _should_retry(error: Exception) -> bool:
        return isinstance(error, LLMCallError) and error.details.get("retryable") == "true"

    def _handle_retryable_failure(error: LLMCallError) -> str | None:
        if breaker is not None and error.details.get("retryable") == "true":
            breaker.record_failure()
            if breaker.opened_until > 0:
                emit_recovery_alert(
                    trace_id=trace_id or "none",
                    source_type="llm",
                    source_name=f"{settings.provider}:{settings.model}",
                    severity="error",
                    event_code="llm_circuit_opened",
                    message="模型连续失败已触发熔断。",
                    payload={
                        "provider": settings.provider,
                        "model": settings.model,
                        "failure_count": breaker.failure_count,
                    },
                )
            else:
                emit_recovery_alert(
                    trace_id=trace_id or "none",
                    source_type="llm",
                    source_name=f"{settings.provider}:{settings.model}",
                    severity="warning",
                    event_code="llm_retry_exhausted" if is_llm_retry_enabled() else "llm_request_failed",
                    message="模型重试后仍失败。" if is_llm_retry_enabled() else "模型请求失败。",
                    payload={"provider": settings.provider, "model": settings.model},
                )
            if llm_degrade_to_mock:
                emit_recovery_alert(
                    trace_id=trace_id or "none",
                    source_type="llm",
                    source_name=f"{settings.provider}:{settings.model}",
                    severity="warning",
                    event_code="llm_degraded_to_mock",
                    message="模型失败后已降级到 mock 响应。",
                    payload={"provider": settings.provider, "model": settings.model},
                )
                return _build_mock_response(cleaned_prompt, input_assets, degraded=True)
        return None

    if is_llm_retry_enabled():
        try:
            response = execute_with_retry(
                _invoke,
                attempts=get_llm_retry_attempts(),
                backoff_ms=get_llm_retry_backoff_ms(),
                should_retry=_should_retry,
            )
        except LLMCallError as error:
            degraded_result = _handle_retryable_failure(error)
            if degraded_result is not None:
                return degraded_result
            raise
    else:
        try:
            response = _invoke()
        except LLMCallError as error:
            degraded_result = _handle_retryable_failure(error)
            if degraded_result is not None:
                return degraded_result
            raise

    if breaker is not None:
        breaker.record_success()

    content = sanitize_text(response.choices[0].message.content or "")
    logger.info("模型调用成功 trace_id=%s", trace_id or "none")
    return content
