from __future__ import annotations

from typing import Any

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from utils.logger import logger
from utils.params import parse_params

_CHECK_NODE = "PVP.CheckBattleCount"


def _store_remaining(context: Context, remaining: int) -> None:
    """Store the remaining battle count in the pipeline node config, preserving existing keys."""
    node_data = context.get_node_data(_CHECK_NODE)
    existing: dict[str, Any] = {}
    if node_data:
        action = node_data.get("action")
        if isinstance(action, dict):
            param = action.get("param")
            if isinstance(param, dict):
                cap = param.get("custom_action_param")
                if isinstance(cap, dict):
                    existing = cap
    merged = {**existing, "remaining": remaining}
    context.override_pipeline({_CHECK_NODE: {"action": {"param": {"custom_action_param": merged}}}})


@AgentServer.custom_action("InitPVPBattleCount")
class InitPVPBattleCount(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            params = parse_params(argv.custom_action_param)
        except ValueError as error:
            logger.error("InitPVPBattleCount: {}", error)
            return CustomAction.RunResult(success=False)

        target: Any = params.get("target_count", 1)
        if not isinstance(target, int):
            logger.error("InitPVPBattleCount: target_count 必须是整数，得到: {}", type(target).__name__)
            return CustomAction.RunResult(success=False)

        _store_remaining(context, target)
        logger.info("[PVP] 剩余战斗次数: {}", target)
        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("CheckPVPBattleCount")
class CheckPVPBattleCount(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            params = parse_params(argv.custom_action_param)
        except ValueError as error:
            logger.error("CheckPVPBattleCount: {}", error)
            return CustomAction.RunResult(success=False)

        remaining: Any = params.get("remaining", 0)
        if not isinstance(remaining, int):
            remaining = 0

        remaining -= 1
        if remaining <= 0:
            logger.info("[PVP] 战斗次数已用完，返回主界面")
            context.override_pipeline({_CHECK_NODE: {"next": ["PVP.ReturnMain"]}})
            return CustomAction.RunResult(success=True)

        _store_remaining(context, remaining)
        logger.info("[PVP] 剩余战斗次数: {}", remaining)
        return CustomAction.RunResult(success=True)
