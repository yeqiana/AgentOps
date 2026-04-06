"""
Generic file loading adapter.

What this is:
- The infrastructure-layer adapter for real file inputs.

What it does:
- Reads files from local paths, URLs, Base64, streams, and raw bytes.
- Extracts real text from common text files, DOCX, and PDF when possible.
- Normalizes all file inputs into a stable `InputAsset`.

Why this is done this way:
- File parsing belongs in infrastructure, not in CLI, API routes, or workflow
  nodes.
- A normalized file asset lets prompt building, persistence, and debugging all
  reuse the same structure.
"""

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import zipfile
from dataclasses import dataclass
from io import BufferedIOBase, BytesIO
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from app.domain.models import InputAsset
from app.infrastructure.llm.client import sanitize_text
from app.infrastructure.media.image_loader import OBJECT_URI_SCHEMES


DEFAULT_FILE_PROMPT = "请阅读这个文件，并总结核心内容、结构和需要注意的重点。"
TEXT_MIME_PREFIXES = ("text/",)
TEXT_FILE_SUFFIXES = {
    ".txt",
    ".md",
    ".markdown",
    ".py",
    ".java",
    ".js",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".csv",
    ".html",
    ".htm",
    ".xml",
    ".sql",
    ".log",
}
MAX_INLINE_TEXT_LENGTH = 6000


@dataclass(frozen=True)
class LoadedFile:
    """
    What this is:
    - The internal normalized file object used inside infrastructure.

    What it does:
    - Stores metadata, extracted text, and file locator information.

    Why this is done this way:
    - Different file entrypoints should converge into one internal shape before
      being converted into domain assets.
    """

    name: str
    source: str
    storage_mode: str
    mime_type: str
    size_bytes: int
    sha256: str
    extracted_text: str
    extraction_mode: str
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
    if data.startswith(b"%PDF"):
        return "application/pdf"
    if data.startswith(b"PK\x03\x04"):
        return "application/zip"
    return "application/octet-stream"


def _truncate_text(text: str) -> str:
    cleaned_text = sanitize_text(text)
    if len(cleaned_text) <= MAX_INLINE_TEXT_LENGTH:
        return cleaned_text
    return f"{cleaned_text[:MAX_INLINE_TEXT_LENGTH]} ...[内容已截断]"


def _extract_text_from_docx(data: bytes) -> str:
    with zipfile.ZipFile(BytesIO(data)) as archive:
        xml_bytes = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml_bytes)
    texts = [node.text for node in root.iter() if node.text]
    return "\n".join(texts)


def _extract_text_from_pdf(data: bytes) -> str:
    """
    What this is:
    - A PDF text extraction helper.

    What it does:
    - Uses `pypdf` to read each page and concatenate extracted text.

    Why this is done this way:
    - Formal PDF support is part of the stage-1 enhancement scope, and `pypdf`
      is the lightest stable dependency for this baseline extraction chain.
    """

    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError("当前环境未安装 pypdf。") from error

    reader = PdfReader(BytesIO(data))
    texts: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            texts.append(page_text.strip())
    return "\n".join(texts).strip()


def _extract_text(data: bytes, *, filename: str, mime_type: str) -> tuple[str, str]:
    suffix = Path(filename).suffix.lower()

    if suffix == ".docx":
        try:
            return _truncate_text(_extract_text_from_docx(data)), "docx_xml"
        except Exception:
            return "DOCX 文件读取失败，暂未提取到正文。", "docx_failed"

    if suffix == ".json":
        try:
            parsed = json.loads(data.decode("utf-8"))
            return _truncate_text(json.dumps(parsed, ensure_ascii=False, indent=2)), "json"
        except Exception:
            pass

    if mime_type == "application/pdf" or suffix == ".pdf":
        try:
            extracted_text = _extract_text_from_pdf(data)
            if extracted_text:
                return _truncate_text(extracted_text), "pdf_pypdf"
            return "PDF 文件已读取，但当前未提取到正文内容。", "pdf_empty"
        except Exception as error:
            return f"PDF 文件已读取，但正文提取失败：{sanitize_text(str(error))}", "pdf_failed"

    if mime_type.startswith(TEXT_MIME_PREFIXES) or suffix in TEXT_FILE_SUFFIXES:
        try:
            return _truncate_text(data.decode("utf-8", errors="replace")), "text"
        except Exception:
            return "文件已读取，但文本解码失败。", "text_failed"

    return "文件已读取，但当前格式未接入正文提取器，因此只保留了文件元信息。", "metadata_only"


def load_file_from_bytes(
    data: bytes,
    *,
    name: str = "document.bin",
    source: str = "bytes",
    mime_type: str | None = None,
) -> LoadedFile:
    resolved_mime_type = _detect_mime_type(data, filename=name, mime_type=mime_type)
    extracted_text, extraction_mode = _extract_text(data, filename=name, mime_type=resolved_mime_type)
    return LoadedFile(
        name=name,
        source=source,
        storage_mode="bytes",
        mime_type=resolved_mime_type,
        size_bytes=len(data),
        sha256=_hash_bytes(data),
        extracted_text=extracted_text,
        extraction_mode=extraction_mode,
        data_base64=_encode_base64(data),
    )


def load_file_from_stream(
    stream: BufferedIOBase,
    *,
    name: str = "document-stream.bin",
    source: str = "stream",
    mime_type: str | None = None,
) -> LoadedFile:
    return load_file_from_bytes(stream.read(), name=name, source=source, mime_type=mime_type)


def load_file_from_base64(
    encoded_data: str,
    *,
    name: str = "document-base64.bin",
    source: str = "base64",
    mime_type: str | None = None,
) -> LoadedFile:
    return load_file_from_bytes(
        base64.b64decode(encoded_data),
        name=name,
        source=source,
        mime_type=mime_type,
    )


def load_file_from_local_path(path: str | Path) -> LoadedFile:
    resolved_path = Path(path).expanduser().resolve()
    data = resolved_path.read_bytes()
    loaded_file = load_file_from_bytes(
        data,
        name=resolved_path.name,
        source="local_path",
        mime_type=mimetypes.guess_type(str(resolved_path))[0],
    )
    return LoadedFile(
        name=loaded_file.name,
        source=loaded_file.source,
        storage_mode="local_path",
        mime_type=loaded_file.mime_type,
        size_bytes=loaded_file.size_bytes,
        sha256=loaded_file.sha256,
        extracted_text=loaded_file.extracted_text,
        extraction_mode=loaded_file.extraction_mode,
        data_base64=loaded_file.data_base64,
        local_path=str(resolved_path),
        locator=str(resolved_path),
    )


def load_file_from_url(url: str, *, timeout: int = 15) -> LoadedFile:
    request = Request(url, headers={"User-Agent": "simple-ai-agent/1.0"})
    with urlopen(request, timeout=timeout) as response:
        data = response.read()
        mime_type = response.headers.get_content_type()

    parsed_url = urlparse(url)
    file_name = Path(parsed_url.path).name or "remote-file"
    loaded_file = load_file_from_bytes(data, name=file_name, source="url", mime_type=mime_type)
    return LoadedFile(
        name=loaded_file.name,
        source=loaded_file.source,
        storage_mode="url",
        mime_type=loaded_file.mime_type,
        size_bytes=loaded_file.size_bytes,
        sha256=loaded_file.sha256,
        extracted_text=loaded_file.extracted_text,
        extraction_mode=loaded_file.extraction_mode,
        data_base64=loaded_file.data_base64,
        url=url,
        locator=url,
    )


def build_file_asset(loaded_file: LoadedFile) -> InputAsset:
    asset: InputAsset = {
        "kind": "file",
        "name": sanitize_text(loaded_file.name),
        "content": sanitize_text(
            f"文件名称：{loaded_file.name}；来源：{loaded_file.source}；MIME：{loaded_file.mime_type}；"
            f"大小：{loaded_file.size_bytes} 字节；提取方式：{loaded_file.extraction_mode}。\n"
            f"提取内容：\n{loaded_file.extracted_text}"
        ),
        "source": sanitize_text(loaded_file.source),
        "storage_mode": loaded_file.storage_mode,
        "mime_type": loaded_file.mime_type,
        "size_bytes": loaded_file.size_bytes,
        "sha256": loaded_file.sha256,
    }
    if loaded_file.data_base64:
        asset["data_base64"] = loaded_file.data_base64
    if loaded_file.url:
        asset["url"] = loaded_file.url
    if loaded_file.local_path:
        asset["local_path"] = loaded_file.local_path
    if loaded_file.locator:
        asset["locator"] = loaded_file.locator
    return asset


def is_probable_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_object_storage_uri(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in OBJECT_URI_SCHEMES and bool(parsed.netloc)


def build_file_asset_from_reference(reference: str) -> tuple[str, InputAsset]:
    cleaned_reference = sanitize_text(reference)
    if is_probable_url(cleaned_reference):
        return DEFAULT_FILE_PROMPT, build_file_asset(load_file_from_url(cleaned_reference))

    if is_object_storage_uri(cleaned_reference):
        parsed = urlparse(cleaned_reference)
        asset: InputAsset = {
            "kind": "file",
            "name": Path(parsed.path).name or "object-file",
            "content": (
                f"文件位于对象存储 URI：{cleaned_reference}。"
                "当前运行时不会直接下载该对象；请优先提供预签名 HTTPS URL，"
                "或由上层先把对象读取成字节流再传入 Agent。"
            ),
            "source": "object_uri",
            "storage_mode": "object_uri",
            "locator": cleaned_reference,
        }
        return DEFAULT_FILE_PROMPT, asset

    return DEFAULT_FILE_PROMPT, build_file_asset(load_file_from_local_path(cleaned_reference))
