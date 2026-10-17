"""收集安卓测试包到 dist 并加构建日期后缀

gradlew 产出的 APK 文件名固定（``app-debug.apk`` / ``app-release.apk``），连续构建会互相
覆盖、难以区分。本脚本把指定变体的产物复制到 ``dist/package-maafwapp/``，命名为
``app-<variant>-<YYYYMMDD>.apk``（版本号取自同目录的 output-metadata.json，仅用于校验
提示）。

用法（在仓库根执行，出包并（release 时）跑完 shrink_apk.py 之后）：

    python tools/collect_android_apk.py release
    python tools/collect_android_apk.py debug --date 20261012   # 覆盖日期

默认日期为当天；同一天再次收集会覆盖同名文件（保留最新构建）。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APK_OUTPUT_DIR = PROJECT_ROOT / "Android" / "MaaFwApp" / "app" / "build" / "outputs" / "apk"
DEST_DIR = PROJECT_ROOT / "dist" / "package-maafwapp"


def read_version_name(variant_dir: Path) -> str | None:
    """从 output-metadata.json 读 versionName。"""
    meta = variant_dir / "output-metadata.json"
    if not meta.is_file():
        return None
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
        return data["elements"][0]["versionName"]
    except (KeyError, IndexError, json.JSONDecodeError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect an Android test APK into dist with a build-date suffix")
    parser.add_argument("variant", choices=["debug", "release"], help="构建变体")
    parser.add_argument("--date", help="日期后缀 YYYYMMDD，默认今天")
    args = parser.parse_args()

    stamp = args.date or date.today().strftime("%Y%m%d")
    if not re.fullmatch(r"\d{8}", stamp):
        print(f"日期格式应为 YYYYMMDD: {stamp}", file=sys.stderr)
        return 1

    src = APK_OUTPUT_DIR / args.variant / f"app-{args.variant}.apk"
    if not src.is_file():
        print(f"未找到 {src}", file=sys.stderr)
        return 1

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    dst = DEST_DIR / f"app-{args.variant}-{stamp}.apk"
    shutil.copy2(src, dst)

    version = read_version_name(src.parent)
    version_hint = f"（versionName {version}）" if version else ""
    print(f"已收集: {dst} ({dst.stat().st_size / 1048576:.1f}M){version_hint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
