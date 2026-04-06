"""
API 表现层包。
这是什么：
- 这是后续 HTTP API 的统一入口包。
做什么：
- 暴露 FastAPI 应用工厂。
为什么这么做：
- 让 API 层有正式落点，避免后续把接口代码继续塞进 CLI 或根目录。
"""

from app.presentation.api.app import create_app

__all__ = ["create_app"]
