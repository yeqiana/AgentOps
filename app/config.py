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

DEFAULT_USER_PROFILE = "默认用户，无额外偏好。"
DEFAULT_TASK_STATE = "当前无长期任务状态。"
DEFAULT_OUTPUT_FORMAT = "markdown"
DEFAULT_TONE_STYLE = "专业、简洁、直接"
DEFAULT_VERBOSITY_LEVEL = "中等"


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
