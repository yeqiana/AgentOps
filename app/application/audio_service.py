"""
音频应用服务模块。

这是什么：
- 这是应用层对真实音频入口的统一封装。

做什么：
- 为上层提供“从引用、字节流、Base64 构建音频资产”的入口。

为什么这么做：
- 应用层应该屏蔽底层音频加载和元数据解析细节。
"""

from __future__ import annotations

from io import BufferedIOBase

from app.domain.models import InputAsset
from app.infrastructure.media.audio_loader import (
    DEFAULT_AUDIO_PROMPT,
    build_audio_asset,
    build_audio_asset_from_reference,
    load_audio_from_base64,
    load_audio_from_bytes,
    load_audio_from_stream,
)


def create_audio_asset_from_reference(reference: str) -> tuple[str, InputAsset]:
    return build_audio_asset_from_reference(reference)


def create_audio_asset_from_binary(data: bytes, *, name: str = "audio.bin") -> tuple[str, InputAsset]:
    return DEFAULT_AUDIO_PROMPT, build_audio_asset(load_audio_from_bytes(data, name=name, source="bytes"))


def create_audio_asset_from_base64(
    encoded_data: str,
    *,
    name: str = "audio-base64.bin",
) -> tuple[str, InputAsset]:
    return DEFAULT_AUDIO_PROMPT, build_audio_asset(
        load_audio_from_base64(encoded_data, name=name, source="base64")
    )


def create_audio_asset_from_stream(
    stream: BufferedIOBase,
    *,
    name: str = "audio-stream.bin",
) -> tuple[str, InputAsset]:
    return DEFAULT_AUDIO_PROMPT, build_audio_asset(
        load_audio_from_stream(stream, name=name, source="stream")
    )
