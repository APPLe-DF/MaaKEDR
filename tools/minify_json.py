"""
JSON 压缩工具
压缩项目中的 JSON 文件，减少文件大小
"""

import json
import os
import sys
from pathlib import Path


def minify_json_file(input_path: str, output_path: str = None) -> bool:
    """
    压缩 JSON 文件

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径（默认覆盖原文件）

    Returns:
        是否成功
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if output_path is None:
            output_path = input_path

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

        return True
    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python minify_json.py <file_or_directory>")
        sys.exit(1)

    target = sys.argv[1]

    if os.path.isfile(target):
        if target.endswith('.json'):
            if minify_json_file(target):
                print(f"Minified: {target}")
    elif os.path.isdir(target):
        for root, dirs, files in os.walk(target):
            for file in files:
                if file.endswith('.json'):
                    filepath = os.path.join(root, file)
                    if minify_json_file(filepath):
                        print(f"Minified: {filepath}")


if __name__ == "__main__":
    main()
