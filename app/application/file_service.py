"""
文件应用服务模块。

这是什么：
- 这是应用层对真实文件入口的统一封装。

做什么：
- 为上层提供“从引用、字节流、Base64 构建文件资产”的入口。

为什么这么做：
- CLI、API 和测试都需要文件入口，但不应该直接操作基础设施层细节。
"""

from __future__ import annotations

from io import BufferedIOBase

from app.domain.models import InputAsset
from app.infrastructure.media.file_loader import (
    DEFAULT_FILE_PROMPT,
    build_file_asset,
    build_file_asset_from_reference,
    load_file_from_base64,
    load_file_from_bytes,
    load_file_from_stream,
)


def create_file_asset_from_reference(reference: str) -> tuple[str, InputAsset]:
    return build_file_asset_from_reference(reference)


def create_file_asset_from_binary(data: bytes, *, name: str = "document.bin") -> tuple[str, InputAsset]:
    return DEFAULT_FILE_PROMPT, build_file_asset(load_file_from_bytes(data, name=name, source="bytes"))


def create_file_asset_from_base64(
    encoded_data: str,
    *,
    name: str = "document-base64.bin",
) -> tuple[str, InputAsset]:
    return DEFAULT_FILE_PROMPT, build_file_asset(
        load_file_from_base64(encoded_data, name=name, source="base64")
    )


def create_file_asset_from_stream(
    stream: BufferedIOBase,
    *,
    name: str = "document-stream.bin",
) -> tuple[str, InputAsset]:
    return DEFAULT_FILE_PROMPT, build_file_asset(
        load_file_from_stream(stream, name=name, source="stream")
    )
