"""
Multimodal media service tests.

What this is:
- Integration tests for real audio, video, and file asset parsing.

What it does:
- Verifies WAV metadata parsing, MP4 container parsing, TXT/DOCX text extraction,
  and formal PDF text extraction.

Why this is done this way:
- The value of the multimodal base is not only receiving paths, but proving that
  real resources are actually parsed into useful content.
"""

from __future__ import annotations

import unittest
import wave
import zipfile
from io import BytesIO
from pathlib import Path
import tempfile

from app.application.audio_service import create_audio_asset_from_reference
from app.application.file_service import create_file_asset_from_reference
from app.application.video_service import create_video_asset_from_binary


def _build_minimal_wav_bytes() -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wave_file:
        wave_file.setnchannels(1)
        wave_file.setsampwidth(2)
        wave_file.setframerate(8000)
        wave_file.writeframes(b"\x00\x00" * 800)
    return buffer.getvalue()


def _build_minimal_docx_bytes(text: str) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""",
        )
        archive.writestr(
            "word/document.xml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{text}</w:t></w:r></w:p>
  </w:body>
</w:document>""",
        )
    return buffer.getvalue()


def _build_minimal_mp4_bytes(duration_seconds: int = 2) -> bytes:
    timescale = 1000
    duration = duration_seconds * timescale
    mvhd_payload = (
        b"\x00"
        + b"\x00\x00\x00"
        + b"\x00\x00\x00\x00"
        + b"\x00\x00\x00\x00"
        + timescale.to_bytes(4, "big")
        + duration.to_bytes(4, "big")
        + b"\x00" * 80
    )
    mvhd_size = 8 + len(mvhd_payload)
    mvhd_atom = mvhd_size.to_bytes(4, "big") + b"mvhd" + mvhd_payload
    moov_size = 8 + len(mvhd_atom)
    moov_atom = moov_size.to_bytes(4, "big") + b"moov" + mvhd_atom
    ftyp_payload = b"isom\x00\x00\x02\x00isomiso2"
    ftyp_size = 8 + len(ftyp_payload)
    ftyp_atom = ftyp_size.to_bytes(4, "big") + b"ftyp" + ftyp_payload
    return ftyp_atom + moov_atom


def _build_minimal_pdf_bytes(text: str) -> bytes:
    stream = f"BT /F1 24 Tf 72 72 Td ({text}) Tj ET".encode("utf-8")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
        ),
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF"
        ).encode("ascii")
    )
    return bytes(pdf)


class MediaServiceTests(unittest.TestCase):
    def test_create_audio_asset_from_reference_reads_wav_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / "demo.wav"
            audio_path.write_bytes(_build_minimal_wav_bytes())

            user_prompt, asset = create_audio_asset_from_reference(str(audio_path))

        self.assertIn("请分析这个音频", user_prompt)
        self.assertEqual(asset["kind"], "audio")
        self.assertIn("采样率", asset["content"])

    def test_create_file_asset_from_reference_reads_text_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "demo.txt"
            file_path.write_text("标题\n正文内容", encoding="utf-8")

            user_prompt, asset = create_file_asset_from_reference(str(file_path))

        self.assertIn("请阅读这个文件", user_prompt)
        self.assertEqual(asset["kind"], "file")
        self.assertIn("正文内容", asset["content"])

    def test_create_file_asset_from_reference_reads_docx_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "demo.docx"
            file_path.write_bytes(_build_minimal_docx_bytes("文档正文"))

            _, asset = create_file_asset_from_reference(str(file_path))

        self.assertEqual(asset["kind"], "file")
        self.assertIn("文档正文", asset["content"])

    def test_create_file_asset_from_reference_reads_pdf_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "demo.pdf"
            file_path.write_bytes(_build_minimal_pdf_bytes("Hello PDF"))

            _, asset = create_file_asset_from_reference(str(file_path))

        self.assertEqual(asset["kind"], "file")
        self.assertIn("pdf_pypdf", asset["content"])
        self.assertIn("Hello PDF", asset["content"])

    def test_create_video_asset_from_binary_reads_mp4_duration(self) -> None:
        user_prompt, asset = create_video_asset_from_binary(_build_minimal_mp4_bytes(), name="demo.mp4")

        self.assertIn("请分析这个视频", user_prompt)
        self.assertEqual(asset["kind"], "video")
        self.assertIn("时长", asset["content"])


if __name__ == "__main__":
    unittest.main()
