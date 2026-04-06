"""
图片加载模块。

这是什么：
- 这是基础设施层的真实图片输入适配器。

做什么：
- 支持从本地路径、URL、Base64、流和字节读取图片。
- 抽取图片的基础元信息。
- 构造成统一的 `InputAsset`。

为什么这么做：
- Agent 底座如果要支持真实图片分析，就必须先把不同来源的图片统一成一份稳定结构。
- 这些工作属于基础设施层，不应该让 CLI 或工作流节点直接处理二进制细节。
"""

from __future__ import annotations

import base64
import hashlib
import mimetypes
from dataclasses import dataclass
from io import BufferedIOBase
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.domain.models import InputAsset
from app.infrastructure.llm.client import sanitize_text


OBJECT_URI_SCHEMES = {"s3", "oss", "cos", "gs", "minio"}
DEFAULT_IMAGE_PROMPT = "请分析这张图片的主要内容、关键信息和需要注意的细节。"


@dataclass(frozen=True)
class LoadedImage:
    """
    已标准化的图片对象。

    这是什么：
    - 这是基础设施层内部使用的图片数据对象。

    做什么：
    - 保存图片的来源、MIME、大小、哈希、Base64 内容和定位信息。

    为什么这么做：
    - 先统一成内部对象，再转换为 `InputAsset`，可以让不同图片入口共用同一套处理流程。
    """

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


def _detect_mime_type(data: bytes, *, filename: str | None = None, mime_type: str | None = None) -> str:
    """
    推断图片 MIME 类型。

    这是什么：
    - 这是 MIME 识别辅助函数。

    做什么：
    - 优先使用显式传入的 MIME。
    - 其次根据文件名猜测 MIME。
    - 最后根据图片头部特征推断。

    为什么这么做：
    - 多模态模型接收 data URL 时需要正确的 MIME 类型。
    """
    if mime_type:
        return mime_type

    if filename:
        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type:
            return guessed_type

    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"BM"):
        return "image/bmp"

    return "application/octet-stream"


def _build_description(name: str, source: str, mime_type: str, size_bytes: int) -> str:
    """
    生成图片的结构化描述。

    这是什么：
    - 这是图片元信息文本化函数。

    做什么：
    - 把名称、来源、MIME 和大小整理成一段说明。

    为什么这么做：
    - 即使模型可以直接看图，保留一份结构化文字说明也有利于日志、调试和兜底。
    """
    return f"图片名称：{name}；来源：{source}；MIME：{mime_type}；大小：{size_bytes} 字节。"


def _hash_bytes(data: bytes) -> str:
    """
    计算图片哈希。

    这是什么：
    - 这是图片字节的哈希函数。

    做什么：
    - 生成 SHA-256 哈希值。

    为什么这么做：
    - 哈希便于定位问题、排查重复输入和后续做缓存。
    """
    return hashlib.sha256(data).hexdigest()


def _encode_base64(data: bytes) -> str:
    """
    把图片字节编码成 Base64。

    这是什么：
    - 这是图片二进制到文本的编码函数。

    做什么：
    - 生成不换行的 Base64 字符串。

    为什么这么做：
    - 本地图片和流式图片最终要传给视觉模型时，最通用的办法之一就是 data URL。
    """
    return base64.b64encode(data).decode("ascii")


def load_image_from_bytes(
    data: bytes,
    *,
    name: str = "image.bin",
    source: str = "bytes",
    mime_type: str | None = None,
) -> LoadedImage:
    """
    从字节加载图片。

    这是什么：
    - 这是最底层、最通用的图片加载入口。

    做什么：
    - 接收原始字节并生成标准化图片对象。

    为什么这么做：
    - 不管图片来自本地文件、网络还是对象存储，最终都能落到字节这一层。
    """
    resolved_mime_type = _detect_mime_type(data, filename=name, mime_type=mime_type)
    return LoadedImage(
        name=name,
        source=source,
        storage_mode="bytes",
        mime_type=resolved_mime_type,
        size_bytes=len(data),
        sha256=_hash_bytes(data),
        description=_build_description(name, source, resolved_mime_type, len(data)),
        data_base64=_encode_base64(data),
    )


def load_image_from_stream(
    stream: BufferedIOBase,
    *,
    name: str = "image-stream.bin",
    source: str = "stream",
    mime_type: str | None = None,
) -> LoadedImage:
    """
    从流加载图片。

    这是什么：
    - 这是流式图片入口。

    做什么：
    - 读取流中的全部字节，再复用字节入口。

    为什么这么做：
    - Web 上传、内存流和对象存储下载流都适合走这个入口。
    """
    return load_image_from_bytes(stream.read(), name=name, source=source, mime_type=mime_type)


def load_image_from_base64(
    encoded_data: str,
    *,
    name: str = "image-base64.bin",
    source: str = "base64",
    mime_type: str | None = None,
) -> LoadedImage:
    """
    从 Base64 加载图片。

    这是什么：
    - 这是 Base64 图片入口。

    做什么：
    - 解码 Base64，并复用字节入口。

    为什么这么做：
    - 很多上传接口和消息中转系统会直接给出 Base64 字符串。
    """
    return load_image_from_bytes(
        base64.b64decode(encoded_data),
        name=name,
        source=source,
        mime_type=mime_type,
    )


def load_image_from_local_path(path: str | Path) -> LoadedImage:
    """
    从本地路径加载图片。

    这是什么：
    - 这是命令行场景里最常见的真实图片入口。

    做什么：
    - 读取本地文件并生成标准化图片对象。

    为什么这么做：
    - 本地路径分析是 CLI 工具最直接的使用方式。
    """
    resolved_path = Path(path).expanduser().resolve()
    data = resolved_path.read_bytes()
    image = load_image_from_bytes(
        data,
        name=resolved_path.name,
        source="local_path",
        mime_type=mimetypes.guess_type(str(resolved_path))[0],
    )
    return LoadedImage(
        name=image.name,
        source=image.source,
        storage_mode="local_path",
        mime_type=image.mime_type,
        size_bytes=image.size_bytes,
        sha256=image.sha256,
        description=_build_description(
            resolved_path.name,
            f"本地文件 {resolved_path}",
            image.mime_type,
            image.size_bytes,
        ),
        data_base64=image.data_base64,
        local_path=str(resolved_path),
        locator=str(resolved_path),
    )


def load_image_from_url(url: str, *, timeout: int = 15) -> LoadedImage:
    """
    从 URL 加载图片。

    这是什么：
    - 这是远程图片入口。

    做什么：
    - 下载远程图片并生成标准化图片对象。

    为什么这么做：
    - 预签名 URL、CDN URL 和普通 HTTP 图片链接都适合走这个入口。
    """
    request = Request(url, headers={"User-Agent": "simple-ai-agent/1.0"})
    with urlopen(request, timeout=timeout) as response:
        data = response.read()
        mime_type = response.headers.get_content_type()

    parsed_url = urlparse(url)
    file_name = Path(parsed_url.path).name or "remote-image"
    image = load_image_from_bytes(data, name=file_name, source="url", mime_type=mime_type)
    return LoadedImage(
        name=image.name,
        source=image.source,
        storage_mode="url",
        mime_type=image.mime_type,
        size_bytes=image.size_bytes,
        sha256=image.sha256,
        description=_build_description(file_name, f"远程地址 {url}", image.mime_type, image.size_bytes),
        data_base64=image.data_base64,
        url=url,
        locator=url,
    )


def build_image_asset(loaded_image: LoadedImage) -> InputAsset:
    """
    把内部图片对象转成输入资产。

    这是什么：
    - 这是基础设施层到领域层的适配函数。

    做什么：
    - 把 `LoadedImage` 转换成工作流统一使用的 `InputAsset`。

    为什么这么做：
    - Prompt 层和工作流层只应该依赖领域模型，而不应该直接依赖基础设施内部对象。
    """
    asset: InputAsset = {
        "kind": "image",
        "name": sanitize_text(loaded_image.name),
        "content": sanitize_text(loaded_image.description),
        "source": sanitize_text(loaded_image.source),
        "storage_mode": loaded_image.storage_mode,
        "mime_type": loaded_image.mime_type,
        "size_bytes": loaded_image.size_bytes,
        "sha256": loaded_image.sha256,
    }

    if loaded_image.data_base64:
        asset["data_base64"] = loaded_image.data_base64
    if loaded_image.url:
        asset["url"] = loaded_image.url
    if loaded_image.local_path:
        asset["local_path"] = loaded_image.local_path
    if loaded_image.locator:
        asset["locator"] = loaded_image.locator

    return asset


def is_probable_url(value: str) -> bool:
    """
    判断是否是普通 URL。

    这是什么：
    - 这是 URL 识别辅助函数。

    做什么：
    - 识别 `http://` 和 `https://` 开头的地址。

    为什么这么做：
    - 统一图片引用入口时，需要先判断它走本地路径还是远程 URL。
    """
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_object_storage_uri(value: str) -> bool:
    """
    判断是否是对象存储 URI。

    这是什么：
    - 这是对象存储协议识别函数。

    做什么：
    - 识别 `s3://`、`oss://`、`cos://`、`gs://` 和 `minio://` 这类定位符。

    为什么这么做：
    - 对象存储 URI 既不是普通 URL，也不是本地路径，需要单独识别。
    """
    parsed = urlparse(value)
    return parsed.scheme in OBJECT_URI_SCHEMES and bool(parsed.netloc)


def build_image_asset_from_reference(reference: str) -> tuple[str, InputAsset]:
    """
    从字符串引用构建图片资产。

    这是什么：
    - 这是上层最常用的统一图片入口。

    做什么：
    - 自动判断引用是本地路径、URL 还是对象存储 URI。
    - 对本地路径和 URL 做真实读取。
    - 对对象存储 URI 保留定位信息并给出明确说明。

    为什么这么做：
    - 上层不应该关心底层读取细节，只需要告诉系统“这是一张图片”。
    """
    cleaned_reference = sanitize_text(reference)

    if is_probable_url(cleaned_reference):
        return DEFAULT_IMAGE_PROMPT, build_image_asset(load_image_from_url(cleaned_reference))

    if is_object_storage_uri(cleaned_reference):
        parsed = urlparse(cleaned_reference)
        asset: InputAsset = {
            "kind": "image",
            "name": Path(parsed.path).name or "object-image",
            "content": (
                f"图片位于对象存储 URI：{cleaned_reference}。"
                "当前运行时不会直接下载该对象；请优先提供预签名 HTTPS URL，"
                "或由上层先把对象读取成字节流再传入 Agent。"
            ),
            "source": "object_uri",
            "storage_mode": "object_uri",
            "locator": cleaned_reference,
        }
        return DEFAULT_IMAGE_PROMPT, asset

    return DEFAULT_IMAGE_PROMPT, build_image_asset(load_image_from_local_path(cleaned_reference))
