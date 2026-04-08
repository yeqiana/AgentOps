"""
Configuration helpers.

What this is:
- A single place for repository-wide default runtime settings.

What it does:
- Builds the default runtime capability description.
- Exposes prompt/output defaults used across CLI, API, and workflow.
- Provides the default upload/download directory with environment override support.

Why this is done this way:
- Agent base projects become hard to maintain if runtime defaults are scattered
  across presentation, workflow, and infrastructure layers.
- Upload paths are part of the base runtime contract, so they should be managed
  centrally instead of being hard-coded in API handlers.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.domain.models import RuntimeContext


DEFAULT_UPLOAD_DOWNLOAD_DIR = "/app/download"
UPLOAD_DOWNLOAD_DIR_ENV = "APP_DOWNLOAD_DIR"
AUTH_ENABLED_ENV = "APP_AUTH_ENABLED"
API_KEYS_ENV = "APP_API_KEYS"
BEARER_TOKENS_ENV = "APP_BEARER_TOKENS"
RATE_LIMIT_ENABLED_ENV = "APP_RATE_LIMIT_ENABLED"
RATE_LIMIT_REQUESTS_ENV = "APP_RATE_LIMIT_REQUESTS"
RATE_LIMIT_WINDOW_SECONDS_ENV = "APP_RATE_LIMIT_WINDOW_SECONDS"
IDEMPOTENCY_ENABLED_ENV = "APP_IDEMPOTENCY_ENABLED"
IDEMPOTENCY_TTL_SECONDS_ENV = "APP_IDEMPOTENCY_TTL_SECONDS"
LLM_RETRY_ENABLED_ENV = "APP_LLM_RETRY_ENABLED"
LLM_RETRY_ATTEMPTS_ENV = "APP_LLM_RETRY_ATTEMPTS"
LLM_RETRY_BACKOFF_MS_ENV = "APP_LLM_RETRY_BACKOFF_MS"
TOOL_RETRY_ENABLED_ENV = "APP_TOOL_RETRY_ENABLED"
TOOL_RETRY_ATTEMPTS_ENV = "APP_TOOL_RETRY_ATTEMPTS"
TOOL_RETRY_BACKOFF_MS_ENV = "APP_TOOL_RETRY_BACKOFF_MS"
LLM_CIRCUIT_ENABLED_ENV = "APP_LLM_CIRCUIT_ENABLED"
LLM_CIRCUIT_FAILURE_THRESHOLD_ENV = "APP_LLM_CIRCUIT_FAILURE_THRESHOLD"
LLM_CIRCUIT_RECOVERY_SECONDS_ENV = "APP_LLM_CIRCUIT_RECOVERY_SECONDS"
TOOL_CIRCUIT_ENABLED_ENV = "APP_TOOL_CIRCUIT_ENABLED"
TOOL_CIRCUIT_FAILURE_THRESHOLD_ENV = "APP_TOOL_CIRCUIT_FAILURE_THRESHOLD"
TOOL_CIRCUIT_RECOVERY_SECONDS_ENV = "APP_TOOL_CIRCUIT_RECOVERY_SECONDS"
WORKFLOW_DELIBERATION_ENABLED_ENV = "APP_WORKFLOW_DELIBERATION_ENABLED"
WORKFLOW_DELIBERATION_KEYWORDS_ENV = "APP_WORKFLOW_DELIBERATION_KEYWORDS"
WORKFLOW_SUPPORT_ROLE_NAME_ENV = "APP_WORKFLOW_SUPPORT_ROLE_NAME"
WORKFLOW_SUPPORT_ROLE_INSTRUCTION_ENV = "APP_WORKFLOW_SUPPORT_ROLE_INSTRUCTION"
WORKFLOW_CHALLENGE_ROLE_NAME_ENV = "APP_WORKFLOW_CHALLENGE_ROLE_NAME"
WORKFLOW_CHALLENGE_ROLE_INSTRUCTION_ENV = "APP_WORKFLOW_CHALLENGE_ROLE_INSTRUCTION"
WORKFLOW_ARBITRATION_ROLE_NAME_ENV = "APP_WORKFLOW_ARBITRATION_ROLE_NAME"
WORKFLOW_ARBITRATION_ROLE_INSTRUCTION_ENV = "APP_WORKFLOW_ARBITRATION_ROLE_INSTRUCTION"
WORKFLOW_CRITIC_ROLE_NAME_ENV = "APP_WORKFLOW_CRITIC_ROLE_NAME"
WORKFLOW_CRITIC_ROLE_INSTRUCTION_ENV = "APP_WORKFLOW_CRITIC_ROLE_INSTRUCTION"
ALLOWED_TOOLS_ENV = "APP_ALLOWED_TOOLS"
UPLOAD_MAX_BYTES_ENV = "APP_UPLOAD_MAX_BYTES"
UPLOAD_ALLOWED_KINDS_ENV = "APP_UPLOAD_ALLOWED_KINDS"
RECOVERY_LLM_DEGRADE_TO_MOCK_ENV = "APP_RECOVERY_LLM_DEGRADE_TO_MOCK"
RECOVERY_TOOL_SOFT_FAIL_ENV = "APP_RECOVERY_TOOL_SOFT_FAIL"

DEFAULT_USER_PROFILE = "默认用户，无额外偏好。"
DEFAULT_TASK_STATE = "当前无长期任务状态。"
DEFAULT_OUTPUT_FORMAT = "markdown"
DEFAULT_TONE_STYLE = "专业、简洁、直接"
DEFAULT_VERBOSITY_LEVEL = "中等"
DEFAULT_RATE_LIMIT_REQUESTS = 60
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60
DEFAULT_IDEMPOTENCY_TTL_SECONDS = 300
DEFAULT_RETRY_ATTEMPTS = 2
DEFAULT_RETRY_BACKOFF_MS = 100
DEFAULT_CIRCUIT_FAILURE_THRESHOLD = 3
DEFAULT_CIRCUIT_RECOVERY_SECONDS = 30
DEFAULT_DELIBERATION_KEYWORDS = ["比较", "辩论", "评审", "优缺点", "方案"]
DEFAULT_SUPPORT_ROLE_NAME = "支持方代理"
DEFAULT_SUPPORT_ROLE_INSTRUCTION = "优先指出当前规划与最终回答应保留的强项和有效路径。"
DEFAULT_CHALLENGE_ROLE_NAME = "质疑方代理"
DEFAULT_CHALLENGE_ROLE_INSTRUCTION = "优先指出当前规划可能遗漏的风险、限制、反例或需要澄清的地方。"
DEFAULT_ARBITRATION_ROLE_NAME = "仲裁代理"
DEFAULT_ARBITRATION_ROLE_INSTRUCTION = "优先整理支持与质疑两方的观点，并给出最终可执行的取舍与输出要点。"
DEFAULT_CRITIC_ROLE_NAME = "批评代理"
DEFAULT_CRITIC_ROLE_INSTRUCTION = "优先指出答案的遗漏、风险和说明不足，并给出最关键的修改建议。"
DEFAULT_UPLOAD_MAX_BYTES = 20 * 1024 * 1024
DEFAULT_UPLOAD_ALLOWED_KINDS = ["image", "audio", "video", "file"]
DEFAULT_ALLOWED_TOOLS: list[str] = []
DEFAULT_RECOVERY_LLM_DEGRADE_TO_MOCK = False
DEFAULT_RECOVERY_TOOL_SOFT_FAIL = False


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        return max(1, int(raw_value))
    except ValueError:
        return default


def _get_csv_env(name: str, default: list[str]) -> list[str]:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    values = [item.strip() for item in raw_value.split(",") if item.strip()]
    return values or default


def create_default_runtime_context() -> RuntimeContext:
    """
    What this is:
    - A factory function for the runtime capability snapshot.

    What it does:
    - Declares supported modalities, tool visibility, network assumptions, and
      runtime constraints for the current process.

    Why this is done this way:
    - Prompt building and workflow planning need an explicit capability boundary,
      otherwise the model may overestimate what the runtime can do.
    """

    return {
        "input_modalities": ["text", "image", "audio", "video", "file"],
        "output_modalities": ["text"],
        "tools": [],
        "network_status": "不保证始终可联网，远程 URL 是否可访问取决于当前运行环境。",
        "file_access_status": "允许读取当前工作目录及其子目录中的项目文件。",
        "runtime_constraints": [
            "默认入口包括 CLI 和 HTTP API。",
            "图片、音频、视频、文件都支持本地路径、HTTP/HTTPS URL、Base64 和对象存储 URI。",
            "上传型资产接口会先把文件写入本地目录，再进入统一资产解析与工具链。",
            f"上传文件默认写入 {DEFAULT_UPLOAD_DOWNLOAD_DIR}，也支持通过 {UPLOAD_DOWNLOAD_DIR_ENV} 覆盖。",
            f"上传文件默认大小限制为 {DEFAULT_UPLOAD_MAX_BYTES} 字节，也支持通过 {UPLOAD_MAX_BYTES_ENV} 覆盖。",
            "不要虚构图片、音频、视频或文件中不存在的内容。",
        ],
    }


def get_upload_download_dir() -> Path:
    """
    What this is:
    - A helper that resolves the upload/download root directory.

    What it does:
    - Reads the configured directory from environment variables.
    - Falls back to `/app/download` when no override is provided.

    Why this is done this way:
    - The project needs a stable default path for uploads, but different
      deployments still need to redirect storage to a writable location.
    """

    configured_value = os.getenv(UPLOAD_DOWNLOAD_DIR_ENV, DEFAULT_UPLOAD_DOWNLOAD_DIR).strip()
    if not configured_value:
        configured_value = DEFAULT_UPLOAD_DOWNLOAD_DIR
    return Path(configured_value).expanduser()


def ensure_upload_download_dir() -> Path:
    """
    What this is:
    - A directory initialization helper for upload storage.

    What it does:
    - Resolves the configured upload directory and creates it if needed.

    Why this is done this way:
    - Upload endpoints and OCR-style local tools both depend on a concrete local
      file path, so the directory must exist before files are persisted.
    """

    upload_dir = get_upload_download_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def is_auth_enabled() -> bool:
    return _get_bool_env(AUTH_ENABLED_ENV, default=False)


def get_api_keys() -> list[str]:
    return [item.strip() for item in os.getenv(API_KEYS_ENV, "").split(",") if item.strip()]


def get_bearer_tokens() -> list[str]:
    return [item.strip() for item in os.getenv(BEARER_TOKENS_ENV, "").split(",") if item.strip()]


def is_rate_limit_enabled() -> bool:
    return _get_bool_env(RATE_LIMIT_ENABLED_ENV, default=False)


def get_rate_limit_requests() -> int:
    return _get_int_env(RATE_LIMIT_REQUESTS_ENV, DEFAULT_RATE_LIMIT_REQUESTS)


def get_rate_limit_window_seconds() -> int:
    return _get_int_env(RATE_LIMIT_WINDOW_SECONDS_ENV, DEFAULT_RATE_LIMIT_WINDOW_SECONDS)


def is_idempotency_enabled() -> bool:
    return _get_bool_env(IDEMPOTENCY_ENABLED_ENV, default=False)


def get_idempotency_ttl_seconds() -> int:
    return _get_int_env(IDEMPOTENCY_TTL_SECONDS_ENV, DEFAULT_IDEMPOTENCY_TTL_SECONDS)


def is_llm_retry_enabled() -> bool:
    return _get_bool_env(LLM_RETRY_ENABLED_ENV, default=True)


def get_llm_retry_attempts() -> int:
    return _get_int_env(LLM_RETRY_ATTEMPTS_ENV, DEFAULT_RETRY_ATTEMPTS)


def get_llm_retry_backoff_ms() -> int:
    return _get_int_env(LLM_RETRY_BACKOFF_MS_ENV, DEFAULT_RETRY_BACKOFF_MS)


def is_tool_retry_enabled() -> bool:
    return _get_bool_env(TOOL_RETRY_ENABLED_ENV, default=True)


def get_tool_retry_attempts() -> int:
    return _get_int_env(TOOL_RETRY_ATTEMPTS_ENV, DEFAULT_RETRY_ATTEMPTS)


def get_tool_retry_backoff_ms() -> int:
    return _get_int_env(TOOL_RETRY_BACKOFF_MS_ENV, DEFAULT_RETRY_BACKOFF_MS)


def is_llm_circuit_enabled() -> bool:
    return _get_bool_env(LLM_CIRCUIT_ENABLED_ENV, default=True)


def get_llm_circuit_failure_threshold() -> int:
    return _get_int_env(LLM_CIRCUIT_FAILURE_THRESHOLD_ENV, DEFAULT_CIRCUIT_FAILURE_THRESHOLD)


def get_llm_circuit_recovery_seconds() -> int:
    return _get_int_env(LLM_CIRCUIT_RECOVERY_SECONDS_ENV, DEFAULT_CIRCUIT_RECOVERY_SECONDS)


def is_tool_circuit_enabled() -> bool:
    return _get_bool_env(TOOL_CIRCUIT_ENABLED_ENV, default=True)


def get_tool_circuit_failure_threshold() -> int:
    return _get_int_env(TOOL_CIRCUIT_FAILURE_THRESHOLD_ENV, DEFAULT_CIRCUIT_FAILURE_THRESHOLD)


def get_tool_circuit_recovery_seconds() -> int:
    return _get_int_env(TOOL_CIRCUIT_RECOVERY_SECONDS_ENV, DEFAULT_CIRCUIT_RECOVERY_SECONDS)


def is_workflow_deliberation_enabled() -> bool:
    return _get_bool_env(WORKFLOW_DELIBERATION_ENABLED_ENV, default=True)


def get_workflow_deliberation_keywords() -> list[str]:
    return _get_csv_env(WORKFLOW_DELIBERATION_KEYWORDS_ENV, DEFAULT_DELIBERATION_KEYWORDS)


def get_workflow_support_role_name() -> str:
    return os.getenv(WORKFLOW_SUPPORT_ROLE_NAME_ENV, DEFAULT_SUPPORT_ROLE_NAME).strip() or DEFAULT_SUPPORT_ROLE_NAME


def get_workflow_support_role_instruction() -> str:
    return (
        os.getenv(WORKFLOW_SUPPORT_ROLE_INSTRUCTION_ENV, DEFAULT_SUPPORT_ROLE_INSTRUCTION).strip()
        or DEFAULT_SUPPORT_ROLE_INSTRUCTION
    )


def get_workflow_challenge_role_name() -> str:
    return (
        os.getenv(WORKFLOW_CHALLENGE_ROLE_NAME_ENV, DEFAULT_CHALLENGE_ROLE_NAME).strip()
        or DEFAULT_CHALLENGE_ROLE_NAME
    )


def get_workflow_challenge_role_instruction() -> str:
    return (
        os.getenv(WORKFLOW_CHALLENGE_ROLE_INSTRUCTION_ENV, DEFAULT_CHALLENGE_ROLE_INSTRUCTION).strip()
        or DEFAULT_CHALLENGE_ROLE_INSTRUCTION
    )


def get_workflow_arbitration_role_name() -> str:
    return (
        os.getenv(WORKFLOW_ARBITRATION_ROLE_NAME_ENV, DEFAULT_ARBITRATION_ROLE_NAME).strip()
        or DEFAULT_ARBITRATION_ROLE_NAME
    )


def get_workflow_arbitration_role_instruction() -> str:
    return (
        os.getenv(WORKFLOW_ARBITRATION_ROLE_INSTRUCTION_ENV, DEFAULT_ARBITRATION_ROLE_INSTRUCTION).strip()
        or DEFAULT_ARBITRATION_ROLE_INSTRUCTION
    )


def get_workflow_critic_role_name() -> str:
    return (
        os.getenv(WORKFLOW_CRITIC_ROLE_NAME_ENV, DEFAULT_CRITIC_ROLE_NAME).strip()
        or DEFAULT_CRITIC_ROLE_NAME
    )


def get_workflow_critic_role_instruction() -> str:
    return (
        os.getenv(WORKFLOW_CRITIC_ROLE_INSTRUCTION_ENV, DEFAULT_CRITIC_ROLE_INSTRUCTION).strip()
        or DEFAULT_CRITIC_ROLE_INSTRUCTION
    )


def get_allowed_tools() -> list[str]:
    return _get_csv_env(ALLOWED_TOOLS_ENV, DEFAULT_ALLOWED_TOOLS)


def is_tool_allowed(tool_name: str) -> bool:
    allowed_tools = get_allowed_tools()
    if not allowed_tools:
        return True
    return tool_name in allowed_tools


def get_upload_max_bytes() -> int:
    return _get_int_env(UPLOAD_MAX_BYTES_ENV, DEFAULT_UPLOAD_MAX_BYTES)


def get_upload_allowed_kinds() -> list[str]:
    return _get_csv_env(UPLOAD_ALLOWED_KINDS_ENV, DEFAULT_UPLOAD_ALLOWED_KINDS)


def is_recovery_llm_degrade_to_mock_enabled() -> bool:
    return _get_bool_env(RECOVERY_LLM_DEGRADE_TO_MOCK_ENV, default=DEFAULT_RECOVERY_LLM_DEGRADE_TO_MOCK)


def is_recovery_tool_soft_fail_enabled() -> bool:
    return _get_bool_env(RECOVERY_TOOL_SOFT_FAIL_ENV, default=DEFAULT_RECOVERY_TOOL_SOFT_FAIL)
