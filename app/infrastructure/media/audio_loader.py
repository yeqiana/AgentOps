"""
音频加载模块。

这是什么：
- 这是基础设施层的真实音频输入适配器。

做什么：
- 支持从本地路径、URL、Base64、流和字节读取音频。
- 对 WAV 做真实元数据解析。
- 对其他格式保留基础元信息并明确说明限制。

为什么这么做：
- 音频不能继续只做文本模拟，底座至少需要先具备真实读取和基础解析能力。
- 当前环境没有额外编解码库时，先把可稳定落地的 WAV 能力做好，比假装“全格式都支持”更可靠。
"""

from __future__ import annotations

import base64
import hashlib
import mimetypes
import wave
from dataclasses import dataclass
from io import BufferedIOBase, BytesIO
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.domain.models import InputAsset
from app.infrastructure.llm.client import sanitize_text
from app.infrastructure.media.image_loader import OBJECT_URI_SCHEMES


DEFAULT_AUDIO_PROMPT = "请分析这个音频的结构、时长、关键信息和需要进一步处理的内容。"


@dataclass(frozen=True)
class LoadedAudio:
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
    if data.startswith(b"RIFF") and data[8:12] == b"WAVE":
        return "audio/wav"
    if data.startswith(b"ID3") or data[:2] == b"\xff\xfb":
        return "audio/mpeg"
    if data.startswith(b"OggS"):
        return "audio/ogg"
    return "application/octet-stream"


def _build_audio_description(name: str, source: str, mime_type: str, size_bytes: int, data: bytes) -> str:
    if mime_type == "audio/wav":
        try:
            with wave.open(BytesIO(data), "rb") as wave_file:
                channels = wave_file.getnchannels()
                sample_width = wave_file.getsampwidth()
                frame_rate = wave_file.getframerate()
                frame_count = wave_file.getnframes()
                duration_seconds = frame_count / frame_rate if frame_rate else 0
            return (
                f"音频名称：{name}；来源：{source}；MIME：{mime_type}；大小：{size_bytes} 字节；"
                f"声道数：{channels}；采样率：{frame_rate} Hz；采样宽度：{sample_width} 字节；"
                f"时长：{duration_seconds:.2f} 秒。"
            )
        except Exception:
            return (
                f"音频名称：{name}；来源：{source}；MIME：{mime_type}；大小：{size_bytes} 字节；"
                "WAV 读取失败，当前仅保留了基础元信息。"
            )

    return (
        f"音频名称：{name}；来源：{source}；MIME：{mime_type}；大小：{size_bytes} 字节；"
        "当前环境未集成该格式的完整解码器，因此仅保留基础元信息。"
    )


def load_audio_from_bytes(
    data: bytes,
    *,
    name: str = "audio.bin",
    source: str = "bytes",
    mime_type: str | None = None,
) -> LoadedAudio:
    resolved_mime_type = _detect_mime_type(data, filename=name, mime_type=mime_type)
    return LoadedAudio(
        name=name,
        source=source,
        storage_mode="bytes",
        mime_type=resolved_mime_type,
        size_bytes=len(data),
        sha256=_hash_bytes(data),
        description=_build_audio_description(name, source, resolved_mime_type, len(data), data),
        data_base64=_encode_base64(data),
    )


def load_audio_from_stream(
    stream: BufferedIOBase,
    *,
    name: str = "audio-stream.bin",
    source: str = "stream",
    mime_type: str | None = None,
) -> LoadedAudio:
    return load_audio_from_bytes(stream.read(), name=name, source=source, mime_type=mime_type)


def load_audio_from_base64(
    encoded_data: str,
    *,
    name: str = "audio-base64.bin",
    source: str = "base64",
    mime_type: str | None = None,
) -> LoadedAudio:
    return load_audio_from_bytes(base64.b64decode(encoded_data), name=name, source=source, mime_type=mime_type)


def load_audio_from_local_path(path: str | Path) -> LoadedAudio:
    resolved_path = Path(path).expanduser().resolve()
    data = resolved_path.read_bytes()
    loaded_audio = load_audio_from_bytes(
        data,
        name=resolved_path.name,
        source="local_path",
        mime_type=mimetypes.guess_type(str(resolved_path))[0],
    )
    return LoadedAudio(
        name=loaded_audio.name,
        source=loaded_audio.source,
        storage_mode="local_path",
        mime_type=loaded_audio.mime_type,
        size_bytes=loaded_audio.size_bytes,
        sha256=loaded_audio.sha256,
        description=loaded_audio.description.replace("来源：local_path", f"来源：本地文件 {resolved_path}"),
        data_base64=loaded_audio.data_base64,
        local_path=str(resolved_path),
        locator=str(resolved_path),
    )


def load_audio_from_url(url: str, *, timeout: int = 15) -> LoadedAudio:
    request = Request(url, headers={"User-Agent": "simple-ai-agent/1.0"})
    with urlopen(request, timeout=timeout) as response:
        data = response.read()
        mime_type = response.headers.get_content_type()

    parsed_url = urlparse(url)
    file_name = Path(parsed_url.path).name or "remote-audio"
    loaded_audio = load_audio_from_bytes(data, name=file_name, source="url", mime_type=mime_type)
    return LoadedAudio(
        name=loaded_audio.name,
        source=loaded_audio.source,
        storage_mode="url",
        mime_type=loaded_audio.mime_type,
        size_bytes=loaded_audio.size_bytes,
        sha256=loaded_audio.sha256,
        description=loaded_audio.description.replace("来源：url", f"来源：远程地址 {url}"),
        data_base64=loaded_audio.data_base64,
        url=url,
        locator=url,
    )


def build_audio_asset(loaded_audio: LoadedAudio) -> InputAsset:
    asset: InputAsset = {
        "kind": "audio",
        "name": sanitize_text(loaded_audio.name),
        "content": sanitize_text(loaded_audio.description),
        "source": sanitize_text(loaded_audio.source),
        "storage_mode": loaded_audio.storage_mode,
        "mime_type": loaded_audio.mime_type,
        "size_bytes": loaded_audio.size_bytes,
        "sha256": loaded_audio.sha256,
    }
    if loaded_audio.data_base64:
        asset["data_base64"] = loaded_audio.data_base64
    if loaded_audio.url:
        asset["url"] = loaded_audio.url
    if loaded_audio.local_path:
        asset["local_path"] = loaded_audio.local_path
    if loaded_audio.locator:
        asset["locator"] = loaded_audio.locator
    return asset


def is_probable_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_object_storage_uri(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in OBJECT_URI_SCHEMES and bool(parsed.netloc)


def build_audio_asset_from_reference(reference: str) -> tuple[str, InputAsset]:
    cleaned_reference = sanitize_text(reference)
    if is_probable_url(cleaned_reference):
        return DEFAULT_AUDIO_PROMPT, build_audio_asset(load_audio_from_url(cleaned_reference))
    if is_object_storage_uri(cleaned_reference):
        parsed = urlparse(cleaned_reference)
        asset: InputAsset = {
            "kind": "audio",
            "name": Path(parsed.path).name or "object-audio",
            "content": (
                f"音频位于对象存储 URI：{cleaned_reference}。"
                "当前运行时不会直接下载该对象；请优先提供预签名 HTTPS URL，"
                "或由上层先把对象读取成字节流再传入 Agent。"
            ),
            "source": "object_uri",
            "storage_mode": "object_uri",
            "locator": cleaned_reference,
        }
        return DEFAULT_AUDIO_PROMPT, asset
    return DEFAULT_AUDIO_PROMPT, build_audio_asset(load_audio_from_local_path(cleaned_reference))
