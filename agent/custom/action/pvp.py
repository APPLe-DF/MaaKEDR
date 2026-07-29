from __future__ import annotations

from typing import Any

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from utils.logger import logger
from utils.params import is_int_value, parse_params

# session_remaining 以 context.tasker 唯一标识为 key，避免跨任务干扰。
# 同一 tasker 实例的不同 context 共享同一状态，确保整个任务流程计数一致。
_session_remaining: dict[int, int] = {}


def _session_key(context: Context) -> int:
    """获取当前 session 的唯一标识。"""
    return id(context.tasker)


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

        _session_remaining[_session_key(context)] = target
        logger.info("[PVP] 剩余战斗次数: {}", target)
        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("CheckPVPBattleCount")
class CheckPVPBattleCount(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        key = _session_key(context)
        if key not in _session_remaining:
            logger.error("CheckPVPBattleCount: remaining 未初始化，请先调用 InitPVPBattleCount")
            return CustomAction.RunResult(success=False)

        remaining = _session_remaining[key] - 1

        if remaining <= 0:
            logger.info("[PVP] 战斗次数已用完，返回主界面")
            _session_remaining.pop(key, None)
            context.override_pipeline({"PVP.CheckBattleCount": {"next": ["PVP.ReturnMain"]}})
            return CustomAction.RunResult(success=True)

        _session_remaining[key] = remaining
        logger.info("[PVP] 剩余战斗次数: {}", remaining)
        return CustomAction.RunResult(success=True)
