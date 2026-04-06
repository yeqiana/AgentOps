"""
视频应用服务模块。

这是什么：
- 这是应用层对真实视频入口的统一封装。

做什么：
- 为上层提供“从引用、字节流、Base64 构建视频资产”的入口。

为什么这么做：
- 应用层应该屏蔽底层视频容器解析和标准化细节。
"""

from __future__ import annotations

from io import BufferedIOBase

from app.domain.models import InputAsset
from app.infrastructure.media.video_loader import (
    DEFAULT_VIDEO_PROMPT,
    build_video_asset,
    build_video_asset_from_reference,
    load_video_from_base64,
    load_video_from_bytes,
    load_video_from_stream,
)


def create_video_asset_from_reference(reference: str) -> tuple[str, InputAsset]:
    return build_video_asset_from_reference(reference)


def create_video_asset_from_binary(data: bytes, *, name: str = "video.bin") -> tuple[str, InputAsset]:
    return DEFAULT_VIDEO_PROMPT, build_video_asset(load_video_from_bytes(data, name=name, source="bytes"))


def create_video_asset_from_base64(
    encoded_data: str,
    *,
    name: str = "video-base64.bin",
) -> tuple[str, InputAsset]:
    return DEFAULT_VIDEO_PROMPT, build_video_asset(
        load_video_from_base64(encoded_data, name=name, source="base64")
    )


def create_video_asset_from_stream(
    stream: BufferedIOBase,
    *,
    name: str = "video-stream.bin",
) -> tuple[str, InputAsset]:
    return DEFAULT_VIDEO_PROMPT, build_video_asset(
        load_video_from_stream(stream, name=name, source="stream")
    )
