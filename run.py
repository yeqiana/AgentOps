"""
程序根入口文件。

这是什么：
- 这是项目的最外层启动文件。

做什么：
- 把执行权交给 CLI 表现层入口。

为什么这么做：
- 根入口文件应该尽量薄，只负责启动应用。
- 真正的交互逻辑放到 `presentation` 层，结构会更清晰，也更容易替换成别的入口形式。
"""

from app.presentation.cli import main


if __name__ == "__main__":
    main()
