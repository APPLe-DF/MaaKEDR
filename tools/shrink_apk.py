"""APK 二次瘦身：压缩 dex 条目

AGP 9 默认把 ``classes*.dex`` 以 STORED（不压缩）写进 APK（启动性能取向）。
本脚本在出包之后把 dex 条目改为 deflate 重新打包，再 zipalign + 重签名，
典型收益：release 构建 6.7M dex -> 约 1.8M（整包再省约 5M）。

压缩是无损的，签名由 apksigner 重新生成（沿用构建时用的 keystore）。
用法（在仓库根执行）：

    python tools/shrink_apk.py <输入.apk> [-o 输出.apk]

签名材料默认从 ``Android/MaaFwApp/local.properties`` 读 KEYSTORE_PATH /
KEYSTORE_PASSWORD / KEY_ALIAS / KEY_PASSWORD，也可用参数覆盖。
Android SDK 位置从 local.properties 的 sdk.dir 或 ANDROID_HOME 环境变量解析。
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_PROPERTIES = PROJECT_ROOT / "Android" / "MaaFwApp" / "local.properties"
DEX_PATTERN = re.compile(r"^classes\d*\.dex$")


def read_local_properties(path: Path) -> dict[str, str]:
    """解析 local.properties（Java properties 格式）。"""
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().replace("\\:", ":").replace("\\\\", "\\")
    return result


def find_android_tools(props: dict[str, str]) -> tuple[Path, Path]:
    """定位 zipalign 与 apksigner。

    Windows 上是 ``zipalign.exe`` / ``apksigner.bat``，macOS / Linux 上是不带扩展名的
    可执行文件——CI 的 release 跑在 macos-latest，写死 .exe 会让那一步直接报"缺少工具"。
    """
    sdk = props.get("sdk.dir") or os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not sdk:
        raise SystemExit("找不到 Android SDK：请在 local.properties 配 sdk.dir 或设置 ANDROID_HOME")
    # 空目录时 [-1] 会抛 IndexError，报错指向 glob 而不是"没装 build-tools"，很难懂
    candidates = sorted((Path(sdk) / "build-tools").glob("*"))
    if not candidates:
        raise SystemExit(f"{sdk} 下没有 build-tools：用 sdkmanager 装一个（如 build-tools;37.0.0）")
    build_tools = candidates[-1]

    if sys.platform.startswith("win"):
        zipalign, apksigner = build_tools / "zipalign.exe", build_tools / "apksigner.bat"
    else:
        zipalign, apksigner = build_tools / "zipalign", build_tools / "apksigner"

    if not zipalign.is_file() or not apksigner.is_file():
        raise SystemExit(f"build-tools 目录缺少 zipalign/apksigner: {build_tools}")
    return zipalign, apksigner


def repack(src: Path, dst: Path) -> tuple[int, int]:
    """重写 zip：dex 改 deflate，其余原样拷贝。返回 (dex 原大小, dex 压缩后大小)。

    注意：zipfile.writestr() 会对传入的数据按 compress_type 再压缩一次，所以 dex 必须传
    **未压缩的原始数据**并指定 compresslevel；手动预压缩再传入会导致双重压缩、解出来是
    内层压缩流而不是 dex 本体（设备上表现为 "Invalid or truncated dex file"）。
    """
    dex_before = dex_after = 0
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", allowZip64=True) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            new_info = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            new_info.external_attr = info.external_attr
            new_info.internal_attr = info.internal_attr
            new_info.create_system = info.create_system
            if DEX_PATTERN.match(info.filename):
                dex_before += len(data)
                zout.writestr(new_info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            else:
                zout.writestr(new_info, data, compress_type=info.compress_type)
    with zipfile.ZipFile(dst) as z:
        dex_after = sum(i.compress_size for i in z.infolist() if DEX_PATTERN.match(i.filename))
    return dex_before, dex_after


def verify(src: Path, dst: Path) -> None:
    """校验重打包结果：所有条目内容逐字节一致，dex 以魔数开头。"""
    with zipfile.ZipFile(src) as zs, zipfile.ZipFile(dst) as zd:
        src_hashes = {i.filename: hashlib.sha256(zs.read(i.filename)).hexdigest() for i in zs.infolist()}
        for info in zd.infolist():
            data = zd.read(info.filename)
            digest = hashlib.sha256(data).hexdigest()
            if src_hashes.get(info.filename) != digest:
                raise SystemExit(f"校验失败：{info.filename} 内容与源不一致")
            if DEX_PATTERN.match(info.filename) and not data.startswith(b"dex\n"):
                raise SystemExit(f"校验失败：{info.filename} 不是合法 dex（缺少 dex 魔数）")
    print("内容校验通过：全部条目一致，dex 魔数正常")


def main() -> int:
    parser = argparse.ArgumentParser(description="Recompress dex entries in an APK and re-sign it")
    parser.add_argument("apk", help="输入 APK（gradlew 产物）")
    parser.add_argument("-o", "--output", help="输出 APK，默认覆盖输入")
    args = parser.parse_args()

    src = Path(args.apk)
    dst = Path(args.output) if args.output else src
    if not src.is_file():
        print(f"未找到 {src}", file=sys.stderr)
        return 1

    props = read_local_properties(LOCAL_PROPERTIES)
    zipalign, apksigner = find_android_tools(props)

    # 签名材料：环境变量优先，其次 local.properties（与 MaaFwApp 的 signingSetting 同序）。
    # CI 里没有 local.properties 的 KEYSTORE_PATH——keystore 由 secrets 解出来后经 env 传入。
    def setting(name: str, default: str = "") -> str:
        return os.environ.get(name) or props.get(name) or default

    keystore = setting("KEYSTORE_PATH")

    aligned = src.with_suffix(".aligned.apk")
    tmp = src.with_suffix(".repacked.apk")
    dex_before, dex_after = repack(src, tmp)
    print(f"dex 重压缩: {dex_before / 1048576:.1f}M -> {dex_after / 1048576:.1f}M")
    verify(src, tmp)

    subprocess.run([str(zipalign), "-p", "-f", "4", str(tmp), str(aligned)], check=True)

    # 没有签名材料时不中止：重压缩与对齐仍然有价值（未签名包只是装不上，体积收益照拿）。
    # 之前的写法直接 return 1，会让文档第 7-8 步在未配 keystore 的机器上整段跑不下去。
    if not keystore:
        print(
            "未配置 KEYSTORE_PATH（env 与 local.properties 都没有），跳过签名——"
            "产物为未签名包，不能安装，体积收益已生效",
            file=sys.stderr,
        )
    else:
        # 密码走 apksigner 的 env:<name> 形式，不进 argv：`pass:<明文>` 会让密码出现在
        # 进程参数里（ps / 日志 / CI 的 step 回显都能看到）。apksigner 支持 env: 形式，
        # 我们把值塞进子进程环境再让它按名字读。
        ks_env = "APKSIGNER_KS_PASS"
        key_env = "APKSIGNER_KEY_PASS"
        subprocess.run(
            [
                str(apksigner),
                "sign",
                "--ks",
                keystore,
                "--ks-pass",
                f"env:{ks_env}",
                "--key-pass",
                f"env:{key_env}",
                "--ks-key-alias",
                setting("KEY_ALIAS", "androiddebugkey"),
                str(aligned),
            ],
            check=True,
            env={
                **os.environ,
                ks_env: setting("KEYSTORE_PASSWORD", "android"),
                key_env: setting("KEY_PASSWORD", "android"),
            },
        )
        subprocess.run([str(apksigner), "verify", str(aligned)], check=True, capture_output=True)
        print("签名验证通过")

    shutil.move(str(aligned), dst)
    tmp.unlink(missing_ok=True)
    print(f"输出: {dst} ({dst.stat().st_size / 1048576:.1f}M)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
