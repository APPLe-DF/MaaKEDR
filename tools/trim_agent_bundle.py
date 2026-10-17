"""Agent 运行时瘦身工具

build_agent_bundle.py 产出的 bundle 里有一类对 MaaKEDR 无用的文件：
``prefix/lib`` 下的 sqlite3 相关库（maa 包与 agent 代码均不 import sqlite3）。

**不要删 numpy 的 BLAS**：numpy 的 ``_core/_multiarray_umath`` 与 ``linalg`` 扩展通过
ELF ``DT_NEEDED`` 硬链接 ``libopenblas-*.so``，删掉后 ``import numpy`` 在动态链接阶段
直接失败（Android 上表现为 python3 退出码 1、agent 日志为空）。曾经的瘦身脚本删过它，
已回退并加上依赖自检防止复发。

脚本幂等，可重复执行；删除后会校验没有任何剩余 .so 通过 DT_NEEDED 引用被删文件。

用法（在仓库根执行）：

    python tools/trim_agent_bundle.py [agent-dist 目录]

默认处理 ``Android/agent-dist``，即打包配方里 ``agent.sourceDir`` 指向的目录。
在 ``build_agent_bundle.py`` 之后、``gradlew`` 出包之前执行。
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

DEFAULT_DIST = Path(__file__).resolve().parent.parent / "Android" / "agent-dist"

#: sqlite3 相关（maa 与 agent 均不使用）
SQLITE_LIBS = ("libsqlite3.so", "libsqlite3.so.0", "libsqlite3_python.so")


def remove_matching(directory: Path, patterns: tuple[str, ...]) -> tuple[int, int, set[str]]:
    """删除目录下匹配任一 pattern 的文件，返回 (删除文件数, 删除字节数, 删除的文件名集合)。"""
    count = 0
    total = 0
    removed: set[str] = set()
    if not directory.is_dir():
        return 0, 0, removed
    for pattern in patterns:
        for path in directory.glob(pattern):
            if path.is_file():
                total += path.stat().st_size
                removed.add(path.name)
                path.unlink()
                count += 1
    return count, total, removed


def dt_needed(path: Path) -> list[str]:
    """读取 ELF 的 DT_NEEDED（动态依赖库名）。"""
    data = path.read_bytes()
    if data[:4] != b"\x7fELF":
        return []
    is64 = data[4] == 2
    endian = "<" if data[5] == 1 else ">"
    if is64:
        phoff = struct.unpack_from(endian + "Q", data, 0x20)[0]
        phentsize = struct.unpack_from(endian + "H", data, 0x36)[0]
        phnum = struct.unpack_from(endian + "H", data, 0x38)[0]
    else:
        phoff = struct.unpack_from(endian + "I", data, 0x1C)[0]
        phentsize = struct.unpack_from(endian + "H", data, 0x2A)[0]
        phnum = struct.unpack_from(endian + "H", data, 0x2C)[0]
    segs: list[tuple[int, int, int, int]] = []
    for i in range(phnum):
        off = phoff + i * phentsize
        p_type = struct.unpack_from(endian + "I", data, off)[0]
        if is64:
            p_offset = struct.unpack_from(endian + "Q", data, off + 8)[0]
            p_vaddr = struct.unpack_from(endian + "Q", data, off + 16)[0]
            p_filesz = struct.unpack_from(endian + "Q", data, off + 32)[0]
        else:
            p_offset = struct.unpack_from(endian + "I", data, off + 4)[0]
            p_vaddr = struct.unpack_from(endian + "I", data, off + 8)[0]
            p_filesz = struct.unpack_from(endian + "I", data, off + 16)[0]
        segs.append((p_type, p_offset, p_vaddr, p_filesz))
    dyn = [s for s in segs if s[0] == 2]
    if not dyn:
        return []
    _, d_off, _, d_size = dyn[0]
    entries: list[tuple[int, int]] = []
    for off in range(d_off, d_off + d_size, 16):
        tag, val = struct.unpack_from(endian + "qQ", data, off)
        if tag == 0:
            break
        entries.append((tag, val))
    strtab_va = next((v for t, v in entries if t == 5), None)
    if strtab_va is None:
        return []
    str_off = None
    for p_type, p_offset, p_vaddr, p_filesz in segs:
        if p_type == 1 and p_vaddr <= strtab_va < p_vaddr + p_filesz:
            str_off = p_offset + (strtab_va - p_vaddr)
            break
    if str_off is None:
        return []
    needed: list[str] = []
    for tag, val in entries:
        if tag == 1:
            end = data.index(b"\x00", str_off + val)
            needed.append(data[str_off + val:end].decode("utf-8", "ignore"))
    return needed


def verify_no_dangling_refs(bundle_dir: Path, removed: set[str]) -> None:
    """校验被删文件没有被任何剩余 .so 通过 DT_NEEDED 引用。"""
    if not removed:
        return
    for so in bundle_dir.rglob("*.so"):
        dangling = [name for name in dt_needed(so) if name in removed]
        if dangling:
            raise SystemExit(f"依赖自检失败：{so.relative_to(bundle_dir)} 仍引用已删除的 {dangling}")


def trim_bundle(bundle_dir: Path) -> tuple[int, int]:
    """瘦身单个 abi 的 bundle 目录。"""
    count = 0
    total = 0
    removed: set[str] = set()

    c, t, r = remove_matching(bundle_dir / "prefix" / "lib", SQLITE_LIBS)
    count += c
    total += t
    removed |= r

    # lib-dynload 里的 _sqlite3 扩展模块。路径带 Python 版本号（python3.13），
    # 写死会让内核升到 3.14 后这步静默失效——按目录实际名字找。
    lib_root = bundle_dir / "prefix" / "lib"
    for dynload in sorted(lib_root.glob("python3.*/lib-dynload")):
        for path in dynload.glob("_sqlite3*.so"):
            total += path.stat().st_size
            removed.add(path.name)
            path.unlink()
            count += 1

    verify_no_dangling_refs(bundle_dir, removed)
    return count, total


def main() -> int:
    parser = argparse.ArgumentParser(description="Trim unused native libs from the agent bundle")
    parser.add_argument("dist", nargs="?", default=str(DEFAULT_DIST), help="agent-dist 目录")
    args = parser.parse_args()

    dist = Path(args.dist)
    if not dist.is_dir():
        print(f"未找到 {dist}", file=sys.stderr)
        return 1

    total_count = 0
    total_bytes = 0
    for abi_dir in sorted(dist.iterdir()):
        bundle = abi_dir / "bundle"
        if not bundle.is_dir():
            continue
        count, size = trim_bundle(bundle)
        if count:
            print(f"{abi_dir.name}: 删除 {count} 个文件，释放 {size / 1048576:.1f} MiB（依赖自检通过）")
        else:
            print(f"{abi_dir.name}: 无需清理（已瘦身或不存在目标文件）")
        total_count += count
        total_bytes += size

    print(f"合计：删除 {total_count} 个文件，释放 {total_bytes / 1048576:.1f} MiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
