"""
大模型客户端模块。
这是什么：
- 这是项目统一的模型接入层。
做什么：
- 读取模型配置。
- 创建 OpenAI 兼容客户端。
- 暴露统一的 `call_llm` 接口。
- 在支持视觉输入时，把真实图片资产一起传给模型。
为什么这么做：
- 上层只应该关心“要给模型什么任务和什么输入”，不应该理解 SDK 细节。
- 错误在这里统一翻译成领域错误，更有利于排障。
"""

from __future__ import annotations

import os
import time
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
    模型调用错误。
    这是什么：
    - 模型层对外暴露的统一错误类型。
    做什么：
    - 屏蔽底层 SDK 异常，向上层返回稳定错误对象。
    为什么这么做：
    - 应用层和 API 层不应该依赖第三方 SDK 的异常结构。
    """

    def __init__(self, message: str, trace_id: str | None = None, details: dict[str, str] | None = None) -> None:
        super().__init__(message, trace_id=trace_id, details=details)
        self.code = "llm_call_error"


@dataclass(frozen=True)
class LLMSettings:
    """
    模型配置对象。
    这是什么：
    - LLM 接入层的只读配置模型。
    做什么：
    - 保存 provider、model、api_key 和 base_url。
    为什么这么做：
    - 集中配置比到处传散乱参数更清晰。
    """

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
    """
    清理文本。
    这是什么：
    - 统一的文本清洗函数。
    做什么：
    - 去除非法代理字符并裁剪首尾空白。
    为什么这么做：
    - Windows 终端和外部输入容易带入编码脏数据。
    """
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
    """
    读取并缓存模型配置。
    这是什么：
    - 模型配置读取入口。
    做什么：
    - 从环境变量解析 provider、model、api_key 和 base_url。
    为什么这么做：
    - 同一次运行中配置通常不变，缓存后可以减少重复解析。
    """
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
    """
    获取模型客户端。
    这是什么：
    - OpenAI 兼容客户端的懒加载入口。
    做什么：
    - 根据当前配置创建并缓存客户端。
    为什么这么做：
    - 客户端无需每次调用都重新创建。
    """
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


def call_llm(prompt: str, input_assets: list[InputAsset] | None = None, trace_id: str | None = None) -> str:
    """
    调用大模型并返回文本结果。
    这是什么：
    - 给上层使用的统一模型调用接口。
    做什么：
    - 在 mock 模式下返回本地结果。
    - 在真实模式下走 chat completions。
    - 统一转换底层异常。
    为什么这么做：
    - 保持上层调用简单，也把排障信息统一留在模型层。
    """
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
        has_image_assets = any(asset["kind"] == "image" for asset in (input_assets or []))
        if "仲裁阶段" in cleaned_prompt:
            return "仲裁代理结论：建议保留双方共同认可的关键点，并在最终答案中补充风险与限制说明。"
        if "辩论阶段" in cleaned_prompt:
            if any(keyword in cleaned_prompt for keyword in {"支持方", "强项", "保留", "有效路径"}):
                return "支持方代理观点：当前规划覆盖了主要任务目标，最终答案应优先给出直接结论和关键依据。"
            return "质疑方代理观点：当前规划仍需强调限制条件、失败风险或潜在遗漏，避免结论过度乐观。"
        if "批评阶段" in cleaned_prompt:
            return "批评代理意见：当前结果基本完整，但如果涉及工具失败或明显限制，需要在答案中明确说明。"
        if "规划阶段" in cleaned_prompt:
            if has_image_assets:
                return "这是一个本地 mock 规划结果：先读取图片输入，再结合上下文给出分析。"
            return "这是一个本地 mock 规划结果：先理解任务，再结合上下文生成答案。"
        if has_image_assets:
            return "这是一个本地 mock 最终答案，用于验证真实图片入口和多模态消息拼装是否正常。"
        return "这是一个本地 mock 最终答案，用于验证 Agent 底座流程是否正常。"

    breaker = None
    if settings.provider != "mock" and is_llm_circuit_enabled():
        breaker = get_circuit_breaker(
            f"llm:{settings.provider}:{settings.model}",
            failure_threshold=get_llm_circuit_failure_threshold(),
            recovery_seconds=get_llm_circuit_recovery_seconds(),
        )
        if not breaker.allow_request():
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

    if is_llm_retry_enabled():
        try:
            response = execute_with_retry(
                _invoke,
                attempts=get_llm_retry_attempts(),
                backoff_ms=get_llm_retry_backoff_ms(),
                should_retry=_should_retry,
            )
        except LLMCallError as error:
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
                        event_code="llm_retry_exhausted",
                        message="模型重试后仍失败。",
                        payload={"provider": settings.provider, "model": settings.model},
                    )
            raise
    else:
        try:
            response = _invoke()
        except LLMCallError as error:
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
                        event_code="llm_request_failed",
                        message="模型请求失败。",
                        payload={"provider": settings.provider, "model": settings.model},
                    )
            raise

    if breaker is not None:
        breaker.record_success()

    content = sanitize_text(response.choices[0].message.content or "")
    logger.info("模型调用成功 trace_id=%s", trace_id or "none")
    return content
