"""
Upload application service.

What this is:
- An application-layer service that turns uploaded files into `InputAsset`s.

What it does:
- Infers the asset kind from explicit input, content type, or file suffix.
- Persists the uploaded file into the configured local directory.
- Reuses existing image/audio/video/file services to build normalized assets.

Why this is done this way:
- The API should orchestrate upload flows, not contain storage and asset parsing
  details inline.
- Reusing existing asset builders keeps upload handling aligned with the rest of
  the multimodal runtime.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Literal

from app.application.audio_service import create_audio_asset_from_reference
from app.application.file_service import create_file_asset_from_reference
from app.application.image_service import create_image_asset_from_reference
from app.application.video_service import create_video_asset_from_reference
from app.domain.errors import ValidationError
from app.domain.models import InputAsset
from app.infrastructure.llm.client import sanitize_text
from app.infrastructure.storage.local_upload_store import save_uploaded_bytes


AssetKind = Literal["image", "audio", "video", "file"]

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
VIDEO_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


def infer_asset_kind(
    filename: str,
    *,
    content_type: str = "",
    requested_kind: str = "auto",
) -> AssetKind:
    """
    What this is:
    - A kind inference helper for uploaded assets.

    What it does:
    - Honors an explicit kind when provided.
    - Falls back to content type and file suffix detection.

    Why this is done this way:
    - Upload clients do not always send perfect metadata, so the service needs a
      layered inference strategy instead of relying on a single source.
    """

    normalized_kind = sanitize_text(requested_kind).lower()
    if normalized_kind in {"image", "audio", "video", "file"}:
        return normalized_kind  # type: ignore[return-value]

    normalized_content_type = sanitize_text(content_type).lower()
    if normalized_content_type.startswith("image/"):
        return "image"
    if normalized_content_type.startswith("audio/"):
        return "audio"
    if normalized_content_type.startswith("video/"):
        return "video"

    guessed_content_type, _ = mimetypes.guess_type(filename)
    guessed_type = (guessed_content_type or "").lower()
    if guessed_type.startswith("image/"):
        return "image"
    if guessed_type.startswith("audio/"):
        return "audio"
    if guessed_type.startswith("video/"):
        return "video"

    suffix = Path(filename).suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in AUDIO_SUFFIXES:
        return "audio"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    return "file"


def create_uploaded_asset(
    *,
    filename: str,
    data: bytes,
    content_type: str = "",
    kind: str = "auto",
) -> tuple[str, InputAsset, AssetKind, str]:
    """
    What this is:
    - The main upload orchestration function.

    What it does:
    - Validates the uploaded payload.
    - Saves the file under the configured upload directory.
    - Builds the normalized asset from the saved local path.

    Why this is done this way:
    - Local-path based assets work immediately with OCR/ASR/video tools and keep
      upload flows aligned with existing asset parsing paths.
    """

    cleaned_filename = sanitize_text(filename)
    if not cleaned_filename:
        raise ValidationError("上传文件名不能为空。")
    if not data:
        raise ValidationError("上传文件内容不能为空。")

    inferred_kind = infer_asset_kind(cleaned_filename, content_type=content_type, requested_kind=kind)
    saved_path = save_uploaded_bytes(data, original_filename=cleaned_filename)
    saved_reference = str(saved_path.resolve())

    if inferred_kind == "image":
        prompt, asset = create_image_asset_from_reference(saved_reference)
    elif inferred_kind == "audio":
        prompt, asset = create_audio_asset_from_reference(saved_reference)
    elif inferred_kind == "video":
        prompt, asset = create_video_asset_from_reference(saved_reference)
    else:
        prompt, asset = create_file_asset_from_reference(saved_reference)

    return prompt, asset, inferred_kind, saved_reference
