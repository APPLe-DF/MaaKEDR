from __future__ import annotations

from typing import Any

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from utils.logger import logger
from utils.params import is_int_value, parse_params

# agent 进程由 MaaFW 按任务逐次启动，进程内仅存在单一 tasker；
# 此模块级字典天然限定在单次任务生命周期内，无跨任务干扰风险。
_remaining: int | None = None


@AgentServer.custom_action("InitPVPBattleCount")
class InitPVPBattleCount(CustomAction):
    """
    参数：
    - target_count: 剩余战斗次数（必填，整数或可转换为整数的字符串）
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

        global _remaining
        _remaining = target
        logger.info("[PVP] 剩余战斗次数: {}", target)
        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("CheckPVPBattleCount")
class CheckPVPBattleCount(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        global _remaining
        if _remaining is None:
            logger.error("CheckPVPBattleCount: remaining 未初始化，请先调用 InitPVPBattleCount")
            return CustomAction.RunResult(success=False)

        _remaining -= 1

        if _remaining <= 0:
            logger.info("[PVP] 战斗次数已用完，返回主界面")
            _remaining = None
            context.override_pipeline({"PVP.CheckBattleCount": {"next": ["PVP.ReturnMain"]}})
            return CustomAction.RunResult(success=True)

        logger.info("[PVP] 剩余战斗次数: {}", _remaining)
        return CustomAction.RunResult(success=True)
