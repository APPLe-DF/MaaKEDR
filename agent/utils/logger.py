from __future__ import annotations

import html
import os
import sys
from typing import Any

from loguru import logger
from utils.pienv import client_name
from utils.runtime_paths import get_runtime_paths

LEVEL_SHORT_NAMES = {
    "INFO": "info",
    "ERROR": "err",
    "WARNING": "warn",
    "DEBUG": "debug",
    "CRITICAL": "critical",
    "SUCCESS": "success",
    "TRACE": "trace",
}

ANSI_LEVEL_COLORS = {
    "TRACE": "\033[34m",
    "DEBUG": "\033[36m",
    "INFO": "\033[32m",
    "SUCCESS": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[41m\033[37m",
}

HTML_LEVEL_COLORS = {
    "TRACE": "royalblue",
    "DEBUG": "deepskyblue",
    "INFO": "forestgreen",
    "SUCCESS": "forestgreen",
    "WARNING": "darkorange",
    "ERROR": "crimson",
    "CRITICAL": "firebrick",
}

_has_loguru = False


def _client_name_key() -> str:
    return client_name().strip().upper()


def _is_mfaa_client() -> bool:
    return _client_name_key() == "MFAAVALONIA"


def _is_mxu_client() -> bool:
    return _client_name_key() == "MXU"


def _resolve_console_stream():
    if _is_mxu_client():
        return sys.stdout
    return sys.stderr


def _resolve_console_format() -> str:
    if _is_mfaa_client():
        return "{extra[level_short]}:{message}"
    if _is_mxu_client():
        return "{extra[mxu_html_message]}"
    return "{extra[level_color]}{message}{extra[color_reset]}"


def _short_level_name(level_name: str) -> str:
    return LEVEL_SHORT_NAMES.get(level_name, level_name.lower())


def _ansi_level_color(level_name: str) -> str:
    return ANSI_LEVEL_COLORS.get(level_name, "")


def _format_mxu_html_message(level_name: str, message: str) -> str:
    color = HTML_LEVEL_COLORS.get(level_name, "inherit")
    escaped = html.escape(message)
    lines = escaped.split("\n")
    wrapped = [f'<span style="color:{color};">{line}</span>' for line in lines]
    return "\n".join(wrapped)


def _enrich_record(record: Any) -> bool:
    level_name = record["level"].name
    level_color = _ansi_level_color(level_name)

    record["extra"]["level_short"] = _short_level_name(level_name)
    record["extra"]["level_color"] = level_color
    record["extra"]["color_reset"] = "\033[0m" if level_color else ""
    record["extra"]["mxu_html_message"] = _format_mxu_html_message(level_name, str(record["message"]))
    return True


def _setup_loguru_logger(log_dir: str | None = None, console_level: str = "INFO"):
    paths = get_runtime_paths()
    log_dir = log_dir or str(paths.debug_dir / "custom")
    os.makedirs(log_dir, exist_ok=True)

    logger.remove()

    logger.add(
        _resolve_console_stream(),
        format=_resolve_console_format(),
        colorize=False,
        level=console_level,
        filter=_enrich_record,
    )
    logger.add(
        f"{log_dir}/{{time:YYYY-MM-DD}}.log",
        rotation="00:00",
        retention="2 weeks",
        compression="zip",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        filter=_enrich_record,
    )


# 初始化（模块导入时自动配置）
_setup_loguru_logger()

__all__ = ["logger"]
