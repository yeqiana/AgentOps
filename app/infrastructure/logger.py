"""
日志模块。

这是什么：
- 这是项目统一的日志配置与输出入口。

做什么：
- 根据环境变量初始化日志系统。
- 提供模块级 logger 获取函数。
- 统一控制日志是否开启、日志级别、日志输出位置。

为什么这么做：
- 工程化项目不能依赖零散的 `print` 做调试。
- 引入统一日志层后，CLI、应用服务、工作流和模型接入都可以使用同一套日志能力。
"""

import logging
import os
from pathlib import Path


LOGGER_NAME = "simple_ai_agent"
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "agent.log"
_LOGGER_INITIALIZED = False


def _is_logging_enabled() -> bool:
    value = os.getenv("LOG_ENABLED", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _get_log_level() -> int:
    level_name = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    return getattr(logging, level_name, logging.INFO)


def _get_log_file_path() -> Path:
    configured_path = os.getenv("LOG_FILE_PATH", "").strip()
    if configured_path:
        return Path(configured_path)
    return Path(DEFAULT_LOG_DIR) / DEFAULT_LOG_FILE


def configure_logging() -> logging.Logger:
    """
    初始化日志系统。

    这是什么：
    - 这是日志系统初始化入口。

    做什么：
    - 创建项目级 logger。
    - 配置控制台和文件输出。
    - 根据级别过滤日志。

    为什么这么做：
    - 统一初始化后，其余模块只关心“写日志”，不关心配置细节。
    """
    global _LOGGER_INITIALIZED

    logger = logging.getLogger(LOGGER_NAME)
    if _LOGGER_INITIALIZED:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if not _is_logging_enabled():
        logger.addHandler(logging.NullHandler())
        _LOGGER_INITIALIZED = True
        return logger

    log_level = _get_log_level()
    log_file_path = _get_log_file_path()
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.info("日志系统已启用，级别=%s，文件=%s", logging.getLevelName(log_level), log_file_path)

    _LOGGER_INITIALIZED = True
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    获取 logger。

    这是什么：
    - 这是提供给其他模块的 logger 获取函数。

    做什么：
    - 确保日志系统初始化。
    - 返回主 logger 或子 logger。

    为什么这么做：
    - 不同模块应该有明确日志来源，便于排查问题。
    """
    configure_logging()
    if not name:
        return logging.getLogger(LOGGER_NAME)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")
