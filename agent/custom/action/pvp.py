from __future__ import annotations

from typing import Any

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from utils.logger import logger
from utils.params import is_int_value, merge_node_custom_param, parse_params


@AgentServer.custom_action("InitPVPBattleCount")
class InitPVPBattleCount(CustomAction):
    """
    参数：
    - target_count: 剩余战斗次数（必填，整数或可转换为整数的字符串）
    - target_node: 存储剩余次数的 pipeline 节点名称（默认当前节点）
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            params = parse_params(argv.custom_action_param, "target_count")
        except ValueError as error:
            logger.error("InitPVPBattleCount: {}", error)
            return CustomAction.RunResult(success=False)

        target: Any = params["target_count"]
        if not is_int_value(target):
            try:
                target = int(target)  # type: ignore[arg-type]
                logger.info("InitPVPBattleCount: target_count 由非整数值转换为整数: {}", target)
            except (TypeError, ValueError):
                logger.error("InitPVPBattleCount: target_count 必须是整数，得到: {}", type(target).__name__)
                return CustomAction.RunResult(success=False)

        raw_node = params.get("target_node", argv.node_name)
        if raw_node is not None and not isinstance(raw_node, str):
            logger.warning(
                "InitPVPBattleCount: target_node 配置无效: type={}, value={}，回退到当前节点 {}",
                type(raw_node).__name__,
                raw_node,
                argv.node_name,
            )
            raw_node = argv.node_name
        target_node: str = str(raw_node)
        merge_node_custom_param(context, target_node, {"remaining": target})
        logger.info("[PVP] 节点 {} 剩余战斗次数: {}", target_node, target)
        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("CheckPVPBattleCount")
class CheckPVPBattleCount(CustomAction):
    """
    参数：
    - remaining: 当前剩余战斗次数（必填）
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            params = parse_params(argv.custom_action_param, "remaining")
        except ValueError as error:
            logger.error("CheckPVPBattleCount: {}", error)
            return CustomAction.RunResult(success=False)

        remaining: Any = params["remaining"]
        if not is_int_value(remaining):
            logger.error(
                "CheckPVPBattleCount: remaining 必须是整数，得到: type={}, value={}",
                type(remaining).__name__,
                remaining,
            )
            return CustomAction.RunResult(success=False)

        remaining -= 1
        if remaining <= 0:
            logger.info("[PVP] 节点 {} 战斗次数已用完，返回主界面", argv.node_name)
            context.override_pipeline({argv.node_name: {"next": ["PVP.ReturnMain"]}})
            return CustomAction.RunResult(success=True)

        merge_node_custom_param(context, argv.node_name, {"remaining": remaining})
        logger.info("[PVP] 节点 {} 剩余战斗次数: {}", argv.node_name, remaining)
        return CustomAction.RunResult(success=True)
