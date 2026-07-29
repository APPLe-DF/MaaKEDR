from __future__ import annotations

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from utils.logger import logger
from utils.params import parse_params

_battle_remaining = 0


@AgentServer.custom_action("InitPVPBattleCount")
class InitPVPBattleCount(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        global _battle_remaining
        try:
            params = parse_params(argv.custom_action_param)
        except ValueError as error:
            logger.error("InitPVPBattleCount: {}", error)
            return CustomAction.RunResult(success=False)

        target = params.get("target_count", 1)
        _battle_remaining = target
        logger.info("[PVP] 剩余战斗次数: {}", _battle_remaining)
        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("CheckPVPBattleCount")
class CheckPVPBattleCount(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        global _battle_remaining
        _battle_remaining -= 1
        if _battle_remaining <= 0:
            logger.info("[PVP] 战斗次数已用完，返回主界面")
            context.override_pipeline({"PVP.CheckBattleCount": {"next": ["PVP.ReturnMain"]}})
            return CustomAction.RunResult(success=True)
        logger.info("[PVP] 剩余战斗次数: {}", _battle_remaining)
        return CustomAction.RunResult(success=True)
