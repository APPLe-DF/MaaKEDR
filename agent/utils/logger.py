import sys
import os
from loguru import logger

# 移除默认的 handler
logger.remove()

# 设置 stdout 编码为 UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 添加控制台输出
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
    colorize=True,
    level="INFO",
)

# 添加文件输出（可选）
# debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "debug")
# os.makedirs(debug_dir, exist_ok=True)
# logger.add(
#     os.path.join(debug_dir, "agent_{time:YYYY-MM-DD}.log"),
#     rotation="00:00",
#     retention="7 days",
#     level="DEBUG",
#     format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
#     encoding="utf-8",
# )

__all__ = ["logger"]

# 添加文件输出（可选）
# logger.add(
#     "debug/agent_{time:YYYY-MM-DD}.log",
#     rotation="00:00",
#     retention="7 days",
#     level="DEBUG",
#     format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
#     encoding="utf-8",
# )

__all__ = ["logger"]
