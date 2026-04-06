"""
视频加载模块。

这是什么：
- 这是基础设施层的真实视频输入适配器。

做什么：
- 支持从本地路径、URL、Base64、流和字节读取视频。
- 对 MP4/MOV 和 AVI 做容器级元数据解析。
- 对其他格式保留基础元信息并明确说明限制。

为什么这么做：
- 当前环境没有 ffmpeg 这类外部工具时，先把稳定可用的容器元数据读取做好。
- 容器级解析虽然不等于完整解码，但已经比纯文本模拟前进了一大步，而且能清楚暴露能力边界。
"""

from __future__ import annotations

import base64
import hashlib
import mimetypes
import struct
from dataclasses import dataclass
from io import BufferedIOBase
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.domain.models import InputAsset
from app.infrastructure.llm.client import sanitize_text
from app.infrastructure.media.image_loader import OBJECT_URI_SCHEMES


DEFAULT_VIDEO_PROMPT = "请分析这个视频的结构、时长、关键信息和后续处理建议。"


@dataclass(frozen=True)
class LoadedVideo:
    name: str
    source: str
    storage_mode: str
    mime_type: str
    size_bytes: int
    sha256: str
    description: str
    data_base64: str | None = None
    url: str | None = None
    local_path: str | None = None
    locator: str | None = None


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _encode_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _detect_mime_type(data: bytes, *, filename: str | None = None, mime_type: str | None = None) -> str:
    if mime_type:
        return mime_type
    if filename:
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type:
            return guessed_type
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return "video/mp4"
    if data.startswith(b"RIFF") and data[8:12] == b"AVI ":
        return "video/x-msvideo"
    return "application/octet-stream"


def _read_mp4_duration_seconds(data: bytes) -> float | None:
    marker_position = data.find(b"mvhd")
    if marker_position == -1 or marker_position < 4:
        return None
    atom_offset = marker_position - 4
    atom_size = int.from_bytes(data[atom_offset:marker_position], "big")
    if atom_size < 16 or atom_offset + atom_size > len(data):
        return None
    version = data[marker_position + 4]
    if version == 0:
        timescale = int.from_bytes(data[marker_position + 16 : marker_position + 20], "big")
        duration = int.from_bytes(data[marker_position + 20 : marker_position + 24], "big")
    else:
        timescale = int.from_bytes(data[marker_position + 24 : marker_position + 28], "big")
        duration = int.from_bytes(data[marker_position + 28 : marker_position + 36], "big")
    if timescale:
        return duration / timescale
    return None


def _read_avi_duration_seconds(data: bytes) -> float | None:
    marker = b"avih"
    position = data.find(marker)
    if position == -1 or position + 8 + 56 > len(data):
        return None
    header_start = position + 8
    microseconds_per_frame = struct.unpack_from("<I", data, header_start)[0]
    total_frames = struct.unpack_from("<I", data, header_start + 16)[0]
    if microseconds_per_frame and total_frames:
        return (microseconds_per_frame * total_frames) / 1_000_000
    return None


def _build_video_description(name: str, source: str, mime_type: str, size_bytes: int, data: bytes) -> str:
    duration_seconds = None
    if mime_type in {"video/mp4", "video/quicktime"}:
        duration_seconds = _read_mp4_duration_seconds(data)
    elif mime_type == "video/x-msvideo":
        duration_seconds = _read_avi_duration_seconds(data)

    if duration_seconds is not None:
        return (
            f"视频名称：{name}；来源：{source}；MIME：{mime_type}；大小：{size_bytes} 字节；"
            f"容器解析到的时长：{duration_seconds:.2f} 秒。"
        )

    return (
        f"视频名称：{name}；来源：{source}；MIME：{mime_type}；大小：{size_bytes} 字节；"
        "当前环境未集成完整视频解码器，因此仅保留了容器级或基础元信息。"
    )


def load_video_from_bytes(
    data: bytes,
    *,
    name: str = "video.bin",
    source: str = "bytes",
    mime_type: str | None = None,
) -> LoadedVideo:
    resolved_mime_type = _detect_mime_type(data, filename=name, mime_type=mime_type)
    return LoadedVideo(
        name=name,
        source=source,
        storage_mode="bytes",
        mime_type=resolved_mime_type,
        size_bytes=len(data),
        sha256=_hash_bytes(data),
        description=_build_video_description(name, source, resolved_mime_type, len(data), data),
        data_base64=_encode_base64(data),
    )


def load_video_from_stream(
    stream: BufferedIOBase,
    *,
    name: str = "video-stream.bin",
    source: str = "stream",
    mime_type: str | None = None,
) -> LoadedVideo:
    return load_video_from_bytes(stream.read(), name=name, source=source, mime_type=mime_type)


def load_video_from_base64(
    encoded_data: str,
    *,
    name: str = "video-base64.bin",
    source: str = "base64",
    mime_type: str | None = None,
) -> LoadedVideo:
    return load_video_from_bytes(base64.b64decode(encoded_data), name=name, source=source, mime_type=mime_type)


def load_video_from_local_path(path: str | Path) -> LoadedVideo:
    resolved_path = Path(path).expanduser().resolve()
    data = resolved_path.read_bytes()
    loaded_video = load_video_from_bytes(
        data,
        name=resolved_path.name,
        source="local_path",
        mime_type=mimetypes.guess_type(str(resolved_path))[0],
    )
    return LoadedVideo(
        name=loaded_video.name,
        source=loaded_video.source,
        storage_mode="local_path",
        mime_type=loaded_video.mime_type,
        size_bytes=loaded_video.size_bytes,
        sha256=loaded_video.sha256,
        description=loaded_video.description.replace("来源：local_path", f"来源：本地文件 {resolved_path}"),
        data_base64=loaded_video.data_base64,
        local_path=str(resolved_path),
        locator=str(resolved_path),
    )


def load_video_from_url(url: str, *, timeout: int = 15) -> LoadedVideo:
    request = Request(url, headers={"User-Agent": "simple-ai-agent/1.0"})
    with urlopen(request, timeout=timeout) as response:
        data = response.read()
        mime_type = response.headers.get_content_type()

    parsed_url = urlparse(url)
    file_name = Path(parsed_url.path).name or "remote-video"
    loaded_video = load_video_from_bytes(data, name=file_name, source="url", mime_type=mime_type)
    return LoadedVideo(
        name=loaded_video.name,
        source=loaded_video.source,
        storage_mode="url",
        mime_type=loaded_video.mime_type,
        size_bytes=loaded_video.size_bytes,
        sha256=loaded_video.sha256,
        description=loaded_video.description.replace("来源：url", f"来源：远程地址 {url}"),
        data_base64=loaded_video.data_base64,
        url=url,
        locator=url,
    )


def build_video_asset(loaded_video: LoadedVideo) -> InputAsset:
    asset: InputAsset = {
        "kind": "video",
        "name": sanitize_text(loaded_video.name),
        "content": sanitize_text(loaded_video.description),
        "source": sanitize_text(loaded_video.source),
        "storage_mode": loaded_video.storage_mode,
        "mime_type": loaded_video.mime_type,
        "size_bytes": loaded_video.size_bytes,
        "sha256": loaded_video.sha256,
    }
    if loaded_video.data_base64:
        asset["data_base64"] = loaded_video.data_base64
    if loaded_video.url:
        asset["url"] = loaded_video.url
    if loaded_video.local_path:
        asset["local_path"] = loaded_video.local_path
    if loaded_video.locator:
        asset["locator"] = loaded_video.locator
    return asset


def is_probable_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_object_storage_uri(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in OBJECT_URI_SCHEMES and bool(parsed.netloc)


def build_video_asset_from_reference(reference: str) -> tuple[str, InputAsset]:
    cleaned_reference = sanitize_text(reference)
    if is_probable_url(cleaned_reference):
        return DEFAULT_VIDEO_PROMPT, build_video_asset(load_video_from_url(cleaned_reference))
    if is_object_storage_uri(cleaned_reference):
        parsed = urlparse(cleaned_reference)
        asset: InputAsset = {
            "kind": "video",
            "name": Path(parsed.path).name or "object-video",
            "content": (
                f"视频位于对象存储 URI：{cleaned_reference}。"
                "当前运行时不会直接下载该对象；请优先提供预签名 HTTPS URL，"
                "或由上层先把对象读取成字节流再传入 Agent。"
            ),
            "source": "object_uri",
            "storage_mode": "object_uri",
            "locator": cleaned_reference,
        }
        return DEFAULT_VIDEO_PROMPT, asset
    return DEFAULT_VIDEO_PROMPT, build_video_asset(load_video_from_local_path(cleaned_reference))
