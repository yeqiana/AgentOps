"""
Workflow smoke tests.

What this is:
- Automated tests for the LangGraph main workflow.

What it does:
- Verifies the graph completes a normal mock call.
- Verifies real image assets pass through the workflow.
- Verifies `tool_node` writes tool results back into state.
- Verifies the video post-processing chain can probe, extract a frame, and
  inject the generated frame asset into the workflow state.

Why this is done this way:
- These tests focus on state flow, node connections, and tool-triggered workflow
  behavior instead of model quality.
"""

from __future__ import annotations

import base64
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.application.agent_service import create_initial_state
from app.infrastructure.llm.client import get_llm_client, get_llm_settings
from app.workflow.graph import build_graph


SMALL_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8"
    "/w8AAgMBAp0XG6kAAAAASUVORK5CYII="
)


class WorkflowSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["LLM_PROVIDER"] = "mock"
        get_llm_settings.cache_clear()
        get_llm_client.cache_clear()

    def test_graph_invoke_returns_plan_answer_and_messages(self) -> None:
        graph = build_graph()
        state = create_initial_state()
        state["user_input"] = "帮我写一句简短的自我介绍"
        state["messages"] = [{"role": "user", "content": "帮我写一句简短的自我介绍"}]
        state["input_assets"] = [
            {
                "kind": "text",
                "name": "text_input",
                "content": "帮我写一句简短的自我介绍",
                "source": "test",
                "storage_mode": "inline_text",
            }
        ]

        result = graph.invoke(state)

        self.assertTrue(result["plan"])
        self.assertTrue(result["debate_summary"])
        self.assertTrue(result["arbitration_summary"])
        self.assertTrue(result["answer"])
        self.assertTrue(result["route_name"])
        self.assertTrue(result["critic_summary"])
        self.assertTrue(result["review_status"])
        self.assertGreaterEqual(len(result["messages"]), 2)
        self.assertEqual(result["messages"][-1]["role"], "assistant")

    def test_graph_invoke_accepts_real_image_asset(self) -> None:
        graph = build_graph()
        state = create_initial_state()
        state["user_input"] = "请分析这张图片的内容"
        state["messages"] = [{"role": "user", "content": "请分析这张图片的内容"}]
        state["input_assets"] = [
            {
                "kind": "image",
                "name": "tiny.png",
                "content": "图片名称：tiny.png；来源：bytes；MIME：image/png；大小：68 字节。",
                "source": "bytes",
                "storage_mode": "bytes",
                "mime_type": "image/png",
                "data_base64": SMALL_PNG_BASE64,
                "sha256": "fake",
                "size_bytes": len(base64.b64decode(SMALL_PNG_BASE64)),
            }
        ]

        result = graph.invoke(state)

        self.assertTrue(result["plan"])
        self.assertTrue(result["answer"])
        self.assertEqual(result["route_name"], "image_analysis")
        self.assertIn("当前路由未启用", result["debate_summary"])
        self.assertIn("批评代理", result["critic_summary"])

    def test_graph_invoke_writes_tool_results_when_local_tool_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / "tool_image.png"
            image_path.write_bytes(base64.b64decode(SMALL_PNG_BASE64))

            script_path = Path(temp_dir) / "fake_ocr.cmd"
            script_path.write_text("@echo off\r\necho TOOL OCR RESULT\r\n", encoding="utf-8")

            with patch.dict(os.environ, {"OCR_TOOL_PATH": str(script_path)}, clear=False):
                graph = build_graph()
                state = create_initial_state()
                state["user_input"] = "请分析这张本地图像"
                state["messages"] = [{"role": "user", "content": "请分析这张本地图像"}]
                state["input_assets"] = [
                    {
                        "kind": "image",
                        "name": "tool_image.png",
                        "content": "测试图片",
                        "source": "local_path",
                        "storage_mode": "local_path",
                        "local_path": str(image_path),
                        "locator": str(image_path),
                        "mime_type": "image/png",
                    }
                ]

                result = graph.invoke(state)

        self.assertEqual(len(result["tool_results"]), 1)
        self.assertEqual(result["tool_results"][0]["tool_name"], "ocr_tesseract")
        self.assertIn("TOOL OCR RESULT", result["tool_results"][0]["stdout"])
        self.assertIn("ocr_tesseract", result["task_state"])
        self.assertEqual(result["route_name"], "image_analysis")
        self.assertIn(result["review_status"], {"approved", "needs_attention"})

    def test_deliberation_route_runs_debate_and_arbitration(self) -> None:
        graph = build_graph()
        state = create_initial_state()
        state["user_input"] = "请比较两个方案的优缺点并给出建议"
        state["messages"] = [{"role": "user", "content": "请比较两个方案的优缺点并给出建议"}]
        state["input_assets"] = [
            {
                "kind": "text",
                "name": "text_input",
                "content": "请比较两个方案的优缺点并给出建议",
                "source": "test",
                "storage_mode": "inline_text",
            }
        ]

        result = graph.invoke(state)

        self.assertEqual(result["route_name"], "deliberation_chat")
        self.assertIn("支持方代理", result["debate_summary"])
        self.assertIn("质疑方代理", result["debate_summary"])
        self.assertIn("仲裁代理", result["arbitration_summary"])

    def test_deliberation_route_respects_configured_roles(self) -> None:
        with patch.dict(
            os.environ,
            {
                "APP_WORKFLOW_SUPPORT_ROLE_NAME": "方案支持代理",
                "APP_WORKFLOW_SUPPORT_ROLE_INSTRUCTION": "优先指出方案的优势与收益。",
                "APP_WORKFLOW_CHALLENGE_ROLE_NAME": "方案质疑代理",
                "APP_WORKFLOW_CHALLENGE_ROLE_INSTRUCTION": "优先指出方案的风险与限制。",
            },
            clear=False,
        ):
            graph = build_graph()
            state = create_initial_state()
            state["user_input"] = "请比较两个方案的优缺点并给出建议"
            state["messages"] = [{"role": "user", "content": "请比较两个方案的优缺点并给出建议"}]
            state["input_assets"] = [
                {
                    "kind": "text",
                    "name": "text_input",
                    "content": "请比较两个方案的优缺点并给出建议",
                    "source": "test",
                    "storage_mode": "inline_text",
                }
            ]

            result = graph.invoke(state)

        self.assertEqual(result["route_name"], "deliberation_chat")
        self.assertIn("方案支持代理", result["debate_summary"])
        self.assertIn("方案质疑代理", result["debate_summary"])

    def test_video_post_processing_generates_frame_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "demo.mp4"
            video_path.write_bytes(b"fake video bytes")

            ffprobe_script = Path(temp_dir) / "fake_ffprobe.cmd"
            ffprobe_script.write_text("@echo off\r\necho PROBE RESULT\r\n", encoding="utf-8")

            ffmpeg_script = Path(temp_dir) / "fake_ffmpeg.cmd"
            ffmpeg_script.write_text("@echo off\r\necho frame>%6\r\n", encoding="utf-8")

            ocr_script = Path(temp_dir) / "fake_ocr.cmd"
            ocr_script.write_text("@echo off\r\necho FRAME OCR RESULT\r\n", encoding="utf-8")

            upload_dir = Path(temp_dir) / "uploads"
            with patch.dict(
                os.environ,
                {
                    "VIDEO_PROBE_TOOL_PATH": str(ffprobe_script),
                    "VIDEO_FRAME_TOOL_PATH": str(ffmpeg_script),
                    "OCR_TOOL_PATH": str(ocr_script),
                    "APP_DOWNLOAD_DIR": str(upload_dir),
                },
                clear=False,
            ):
                graph = build_graph()
                state = create_initial_state()
                state["trace_id"] = "trace_video_case"
                state["user_input"] = "请分析这个视频"
                state["messages"] = [{"role": "user", "content": "请分析这个视频"}]
                state["input_assets"] = [
                    {
                        "kind": "video",
                        "name": "demo.mp4",
                        "content": "测试视频",
                        "source": "local_path",
                        "storage_mode": "local_path",
                        "local_path": str(video_path),
                        "locator": str(video_path),
                        "mime_type": "video/mp4",
                    }
                ]

                result = graph.invoke(state)
                tool_names = [item["tool_name"] for item in result["tool_results"]]
                self.assertIn("video_ffprobe", tool_names)
                self.assertIn("video_ffmpeg_frame", tool_names)
                self.assertIn("ocr_tesseract", tool_names)
                self.assertGreaterEqual(len(result["input_assets"]), 2)
                generated_frame_assets = [asset for asset in result["input_assets"] if asset["source"] == "video_frame"]
                self.assertEqual(len(generated_frame_assets), 1)
                self.assertTrue(Path(generated_frame_assets[0]["local_path"]).exists())

    def test_video_post_processing_can_extract_audio_and_run_asr(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "demo.mp4"
            video_path.write_bytes(b"fake video bytes")

            ffprobe_script = Path(temp_dir) / "fake_ffprobe.cmd"
            ffprobe_script.write_text("@echo off\r\necho PROBE RESULT\r\n", encoding="utf-8")

            ffmpeg_script = Path(temp_dir) / "fake_ffmpeg.cmd"
            ffmpeg_script.write_text("@echo off\r\necho audio>%7\r\n", encoding="utf-8")

            whisper_script = Path(temp_dir) / "fake_whisper.cmd"
            whisper_script.write_text("@echo off\r\necho ASR RESULT\r\n", encoding="utf-8")

            upload_dir = Path(temp_dir) / "uploads"
            with patch.dict(
                os.environ,
                {
                    "VIDEO_PROBE_TOOL_PATH": str(ffprobe_script),
                    "VIDEO_AUDIO_TOOL_PATH": str(ffmpeg_script),
                    "ASR_TOOL_PATH": str(whisper_script),
                    "APP_DOWNLOAD_DIR": str(upload_dir),
                },
                clear=False,
            ):
                graph = build_graph()
                state = create_initial_state()
                state["trace_id"] = "trace_video_audio_case"
                state["user_input"] = "请转写这个视频的音频"
                state["messages"] = [{"role": "user", "content": "请转写这个视频的音频"}]
                state["input_assets"] = [
                    {
                        "kind": "video",
                        "name": "demo.mp4",
                        "content": "测试视频",
                        "source": "local_path",
                        "storage_mode": "local_path",
                        "local_path": str(video_path),
                        "locator": str(video_path),
                        "mime_type": "video/mp4",
                    }
                ]

                result = graph.invoke(state)
                tool_names = [item["tool_name"] for item in result["tool_results"]]
                self.assertIn("video_ffprobe", tool_names)
                self.assertIn("video_ffmpeg_audio", tool_names)
                self.assertIn("asr_whisper", tool_names)


if __name__ == "__main__":
    unittest.main()
