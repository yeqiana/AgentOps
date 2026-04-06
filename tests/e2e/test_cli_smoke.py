"""
CLI 冒烟测试。

这是什么：
- 这是对命令行入口的自动化测试文件。

做什么：
- 通过子进程执行 `run.py`。
- 验证程序可以启动、处理输入并正常退出。

为什么这么做：
- 对 CLI 项目来说，仅测内部函数不够，至少要有一条真实入口级冒烟测试。
"""

import os
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class CliSmokeTests(unittest.TestCase):
    """
    CLI 冒烟测试用例。

    这是什么：
    - 这是 `unittest.TestCase` 子类。

    做什么：
    - 启动 CLI 进程，验证标准输入输出链路。

    为什么这么做：
    - CLI 工具经常在入口、编码或循环控制上出问题，这类测试可以尽早发现。
    """

    def test_cli_runs_with_mock_provider(self) -> None:
        env = os.environ.copy()
        env["LLM_PROVIDER"] = "mock"

        process = subprocess.run(
            [sys.executable, "run.py"],
            input="帮我写一句简短的自我介绍\nq\n",
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            cwd=PROJECT_ROOT,
            env=env,
            timeout=30,
        )

        self.assertEqual(process.returncode, 0)
        self.assertIn("Agent Base Runtime", process.stdout)
        self.assertIn("Agent：", process.stdout)
        self.assertIn("已退出对话。", process.stdout)


if __name__ == "__main__":
    unittest.main()
