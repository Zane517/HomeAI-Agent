"""
工具函数 — 日志初始化、异常处理等
"""

import sys
import traceback

from loguru import logger


def setup_logging(level: str = "INFO"):
    """配置 Loguru 日志"""
    logger.remove()  # 移除默认输出
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=level,
        colorize=True,
    )
    logger.add(
        "logs/homeai_{time:YYYY-MM-DD}.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
    )
    return logger


def format_exception(exc: Exception) -> str:
    """格式化异常信息"""
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
