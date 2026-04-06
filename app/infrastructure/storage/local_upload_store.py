"""
Local upload storage adapter.

What this is:
- A filesystem-based storage adapter for uploaded assets.

What it does:
- Persists uploaded bytes into the configured local upload directory.
- Normalizes file names and returns the final saved path.

Why this is done this way:
- OCR, ASR, and video probing tools currently operate on local file paths.
- By keeping file persistence inside `infrastructure/storage`, the API layer
  avoids handling filesystem details directly.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from app.config import ensure_upload_download_dir


_FILENAME_SAFE_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    """
    What this is:
    - A filename normalization helper.

    What it does:
    - Removes path fragments and unsafe characters from user-provided names.
    - Keeps a minimal suffix when available.

    Why this is done this way:
    - Uploaded file names come from external clients and must not be trusted as
      filesystem-safe values.
    """

    raw_name = Path(filename or "upload.bin").name
    normalized = _FILENAME_SAFE_PATTERN.sub("_", raw_name).strip("._")
    return normalized or "upload.bin"


def save_uploaded_bytes(data: bytes, *, original_filename: str) -> Path:
    """
    What this is:
    - The concrete file persistence function for uploaded content.

    What it does:
    - Creates the configured upload directory if missing.
    - Writes the uploaded bytes under a collision-free generated file name.

    Why this is done this way:
    - The API needs a stable local file path for downstream tools, and generated
      names avoid accidental overwrite between requests.
    """

    upload_dir = ensure_upload_download_dir()
    safe_name = sanitize_filename(original_filename)
    suffix = Path(safe_name).suffix
    stem = Path(safe_name).stem or "upload"
    final_name = f"{stem}_{uuid.uuid4().hex}{suffix}"
    saved_path = upload_dir / final_name
    saved_path.write_bytes(data)
    return saved_path
