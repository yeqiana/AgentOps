"""
Upload service tests.

What this is:
- Unit tests for upload configuration and asset creation helpers.

What it does:
- Verifies the default upload directory contract and environment override.
- Verifies uploaded files are converted into normalized assets.

Why this is done this way:
- The upload path is now part of the base runtime contract, so both the default
  and configurable behaviors need direct tests.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.application.upload_service import create_uploaded_asset, infer_asset_kind
from app.config import DEFAULT_UPLOAD_DOWNLOAD_DIR, get_upload_download_dir


class UploadServiceTests(unittest.TestCase):
    """
    What this is:
    - A `unittest.TestCase` suite for upload helpers.

    What it does:
    - Exercises configuration resolution and saved-file asset generation.

    Why this is done this way:
    - Upload handling should stay deterministic even before it is exercised
      through the API layer.
    """

    def test_get_upload_download_dir_uses_default_value(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("APP_DOWNLOAD_DIR", None)
            self.assertEqual(get_upload_download_dir(), Path(DEFAULT_UPLOAD_DOWNLOAD_DIR))

    def test_get_upload_download_dir_supports_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(os.environ, {"APP_DOWNLOAD_DIR": temp_dir}, clear=False):
            self.assertEqual(Path(get_upload_download_dir()), Path(temp_dir))

    def test_infer_asset_kind_prefers_explicit_kind(self) -> None:
        self.assertEqual(infer_asset_kind("sample.bin", requested_kind="video"), "video")

    def test_create_uploaded_asset_saves_file_and_builds_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(os.environ, {"APP_DOWNLOAD_DIR": temp_dir}, clear=False):
            user_input, asset, inferred_kind, saved_path = create_uploaded_asset(
                filename="note.txt",
                data=b"hello upload",
                content_type="text/plain",
                kind="file",
            )
            self.assertEqual(inferred_kind, "file")
            self.assertTrue(user_input)
            self.assertEqual(asset["storage_mode"], "local_path")
            self.assertEqual(asset["local_path"], saved_path)
            self.assertTrue(Path(saved_path).exists())
