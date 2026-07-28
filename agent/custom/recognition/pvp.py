from typing import Any

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from maa.define import RectType
from maa.pipeline import JOCR, JRecognitionType
from utils.logger import logger
from utils.params import parse_params

_battle_remaining = 0


@AgentServer.custom_action("InitPVPBattleCount")
class InitPVPBattleCount(CustomAction):
    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        global _battle_remaining
        params = parse_params(argv.custom_action_param)
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


@AgentServer.custom_recognition("ReadPVPResult")
class ReadPVPResult(CustomRecognition):
    """读取PVP战斗结果"""

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        params = parse_params(argv.custom_recognition_param)

        result_roi = params.get("result_roi", [500, 150, 300, 100])
        current_score_roi = params.get("current_score_roi", [500, 300, 200, 60])
        score_change_roi = params.get("score_change_roi", [710, 300, 100, 60])
        current_rank_roi = params.get("current_rank_roi", [500, 400, 200, 60])
        rank_change_roi = params.get("rank_change_roi", [710, 400, 100, 60])

        image = argv.image

        # OCR识别战斗结果（无颜色过滤）
        result_detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(roi=result_roi, only_rec=True),
            image,
        )

        # 如果识别失败，返回None
        if not result_detail or not result_detail.box:
            return None

        result_text = self._get_text(result_detail)

        # OCR识别积分和排名（使用颜色过滤）
        current_score = self._get_text(
            context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(roi=current_score_roi, only_rec=True, color_filter="PVP.TextFilter"),
                image,
            )
        )
        score_change = self._get_text(
            context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(roi=score_change_roi, only_rec=True, color_filter="PVP.TextFilter"),
                image,
            )
        )
        current_rank = self._get_text(
            context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(roi=current_rank_roi, only_rec=True, color_filter="PVP.TextFilter"),
                image,
            )
        )
        rank_change = self._get_text(
            context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(roi=rank_change_roi, only_rec=True, color_filter="PVP.TextFilter"),
                image,
            )
        )

        # 格式化结果
        score_change_fmt = self._format_change(score_change)
        rank_change_fmt = self._format_change(rank_change)

        # 输出结果
        result_msg = f"{result_text} 积分:{current_score}({score_change_fmt}) 排名:{current_rank}({rank_change_fmt})"
        logger.info("[PVP] {}", result_msg)

        context.override_pipeline(
            {
                "PVP.ExitResult": {
                    "focus": {
                        "Node.Action.Starting": {
                            "content": result_msg,
                            "display": ["log", "toast"],
                        },
                    },
                },
            }
        )

        return CustomRecognition.AnalyzeResult(
            box=result_detail.box,
            detail={
                "result": result_text or "战斗结束",
                "current_score": current_score or "-",
                "score_change": score_change_fmt or "-",
                "current_rank": current_rank or "-",
                "rank_change": rank_change_fmt or "-",
            },
        )

    def _get_text(self, ocr_detail: Any) -> str:
        """从OCR结果中获取文本"""
        if not ocr_detail or not ocr_detail.all_results:
            return ""
        try:
            return ocr_detail.all_results[0].text.strip()  # pyright: ignore
        except AttributeError:
            return ""

    def _format_change(self, text: str) -> str:
        """格式化变化值，确保有正负号"""
        if not text:
            return ""
        # 如果已经有正负号，直接返回
        if text.startswith(("+", "-")):
            return text
        # 否则添加+号
        return f"+{text}"
