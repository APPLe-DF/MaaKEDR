from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from utils.logger import logger

if TYPE_CHECKING:
    from maa.context import Context


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
    从 pipeline 节点定义中安全提取 action.param.custom_action_param。

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


def merge_node_custom_param(
    context: Context,
    node_name: str,
    updates: dict[str, Any],
) -> None:
    """
    安全地将字段合并到 pipeline 节点的 custom_action_param 中。

    读取当前节点的完整 action.param 字典，将 updates 合并到 custom_action_param，
    然后通过 override_pipeline 写回完整的 param（保留 custom_action 等其他字段）。

    Args:
        context: MaaFW Context 对象
        node_name: pipeline 节点名称
        updates: 要合并到 custom_action_param 中的字段
    """
    node_data = context.get_node_data(node_name)
    existing_param: dict[str, Any] = {}
    existing_cap: dict[str, Any] = {}
    if isinstance(node_data, dict):
        action = node_data.get("action")
        if isinstance(action, dict):
            param = action.get("param")
            if isinstance(param, dict):
                existing_param = dict(param)
                cap = param.get("custom_action_param")
                if isinstance(cap, dict):
                    existing_cap = dict(cap)

    merged_cap = {**existing_cap, **updates}
    full_param = {**existing_param, "custom_action_param": merged_cap}
    context.override_pipeline({node_name: {"action": {"param": full_param}}})
