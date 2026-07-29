import json
from typing import Any

from utils.logger import logger


def parse_params(raw: str | None, *required_keys: str) -> dict[str, Any]:
    """
    解析 custom_action_param / custom_recognition_param JSON 字符串。
    支持多层转义的 JSON 字符串。

    Args:
        raw: 原始 JSON 字符串，可为 None 或空串
        required_keys: 必须存在的字段名

    Returns:
        解析后的 dict（raw 为空时返回空 dict）

    Raises:
        ValueError: JSON 格式错误、非对象类型、或缺少必填字段
    """
    if not raw:
        if required_keys:
            raise ValueError(f"参数为空，需要字段: {list(required_keys)}")
        return {}

    # 处理多层转义的 JSON 字符串
    params = raw
    while isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            break

    if not isinstance(params, dict):
        logger.warning(f"parse_params: 参数不是对象，类型: {type(params).__name__}, 值: {params}")
        raise ValueError(f"参数必须是对象，得到: {type(params).__name__}")

    if required_keys:
        missing = [k for k in required_keys if k not in params]
        if missing:
            raise ValueError(f"缺少必填字段: {missing}")

    return params


def extract_custom_param(node_data: dict[str, Any] | None) -> dict[str, Any]:
    """
    从 pipeline 节点定义中安全提取 custom_action_param / custom_recognition_param。

    对嵌套字典结构进行逐层 isinstance 校验，任一层缺失或类型不匹配时返回空 dict。

    Args:
        node_data: context.get_node_data() 返回的节点定义，可为 None

    Returns:
        节点 action.param.custom_action_param 字段（若存在且为 dict），否则空 dict
    """
    if not isinstance(node_data, dict):
        return {}
    action = node_data.get("action")
    if not isinstance(action, dict):
        return {}
    param = action.get("param")
    if not isinstance(param, dict):
        return {}
    cap = param.get("custom_action_param")
    if not isinstance(cap, dict):
        return {}
    return cap
