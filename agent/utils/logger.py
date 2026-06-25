import sys
import os
from loguru import logger

# 移除默认的 handler
logger.remove()

# 设置 stdout 编码为 UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 添加控制台输出（带颜色）
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
    colorize=True,
    level="DEBUG",
)

__all__ = ["logger"]
