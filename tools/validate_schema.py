"""
Schema 验证工具
验证 Pipeline JSON 文件是否符合 MaaFramework 协议
"""

import json
import os
import sys
from pathlib import Path


def validate_json_file(filepath: str) -> dict:
    """
    验证 JSON 文件格式

    Args:
        filepath: 文件路径

    Returns:
        验证结果 {"valid": bool, "error": str}
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json.load(f)
        return {"valid": True, "error": None}
    except json.JSONDecodeError as e:
        return {"valid": False, "error": str(e)}


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_schema.py <file_or_directory>")
        sys.exit(1)

    target = sys.argv[1]
    errors = []

    if os.path.isfile(target):
        if target.endswith('.json'):
            result = validate_json_file(target)
            if not result["valid"]:
                errors.append(f"{target}: {result['error']}")
    elif os.path.isdir(target):
        for root, dirs, files in os.walk(target):
            for file in files:
                if file.endswith('.json'):
                    filepath = os.path.join(root, file)
                    result = validate_json_file(filepath)
                    if not result["valid"]:
                        errors.append(f"{filepath}: {result['error']}")

    if errors:
        print("Validation errors found:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("All JSON files are valid!")


if __name__ == "__main__":
    main()
