"""Android 图标生成工具

从仓库根目录的 logo.ico 生成 MaaFwApp 打包配方（Android/profile.yaml）所需的
logo.png。MaaFwApp 的应用图标只收 png / webp，不接受 ico。

用法（在仓库根执行）：

    python tools/make_android_icon.py

产物为仓库根的 logo.png（幂等覆盖），已在 .gitignore 中；每次构建 APK 前
重新生成本脚本即可，无需提交产物。
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ICON = PROJECT_ROOT / "logo.ico"
TARGET_PNG = PROJECT_ROOT / "logo.png"
TARGET_SIZE = 512


def main() -> int:
    try:
        # Pillow 只是出包工具的可选依赖（不在 pyproject 的运行时依赖里）
        from PIL import Image  # pyright: ignore[reportMissingImports]
    except ImportError:
        print("缺少依赖 Pillow，请先安装：pip install pillow", file=sys.stderr)
        return 1

    if not SOURCE_ICON.is_file():
        print(f"未找到 {SOURCE_ICON}", file=sys.stderr)
        return 1

    with Image.open(SOURCE_ICON) as icon:
        sizes = getattr(icon, "ico", None)
        frames = sorted(sizes.sizes(), reverse=True) if sizes is not None else []
        if frames:
            # 选取 ico 内嵌的最大帧，放大/缩放到 512
            icon.size = frames[0]
        frame = icon.convert("RGBA")
        target = frame.resize((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)
        target.save(TARGET_PNG, format="PNG")

    print(f"已生成 {TARGET_PNG}（{TARGET_SIZE}x{TARGET_SIZE}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
