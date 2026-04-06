"""
音频加载兼容转发模块。

这是什么：
- 这是旧的 `app.infrastructure.audio_loader` 兼容入口。

做什么：
- 把历史导入路径转发到新的 `app.infrastructure.media.audio_loader`。

为什么这么做：
- 当前项目已经把多媒体解析正式分包到 `infrastructure/media/`。
- 保留这个薄转发层可以平滑迁移旧代码和外部引用。
"""

from app.infrastructure.media.audio_loader import *  # noqa: F401,F403
