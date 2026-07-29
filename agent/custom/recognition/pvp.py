from __future__ import annotations

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_recognition import CustomRecognition
from maa.define import RectType
from maa.pipeline import JOCR, JRecognitionType
from utils.logger import logger
from utils.maa_types import ocr_text
from utils.params import parse_params


@AgentServer.custom_recognition("ReadPVPResult")
class ReadPVPResult(CustomRecognition):
    """读取PVP战斗结果"""

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        try:
            params = parse_params(argv.custom_recognition_param)
        except ValueError as error:
            logger.error("ReadPVPResult: {}", error)
            return None

        result_roi = params.get("result_roi", [500, 150, 300, 100])
        current_score_roi = params.get("current_score_roi", [500, 300, 200, 60])
        score_change_roi = params.get("score_change_roi", [710, 300, 100, 60])
        current_rank_roi = params.get("current_rank_roi", [500, 400, 200, 60])
        rank_change_roi = params.get("rank_change_roi", [710, 400, 100, 60])

        image = argv.image

        result_detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(roi=result_roi, only_rec=True),
            image,
        )

        if not result_detail or not result_detail.box:
            return None

        result_text = ocr_text(result_detail)

        current_score = ocr_text(
            context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(roi=current_score_roi, only_rec=True, color_filter="PVP.TextFilter"),
                image,
            )
        )
        score_change = ocr_text(
            context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(roi=score_change_roi, only_rec=True, color_filter="PVP.TextFilter"),
                image,
            )
        )
        current_rank = ocr_text(
            context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(roi=current_rank_roi, only_rec=True, color_filter="PVP.TextFilter"),
                image,
            )
        )
        rank_change = ocr_text(
            context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(roi=rank_change_roi, only_rec=True, color_filter="PVP.TextFilter"),
                image,
            )
        )

        score_change_fmt = self._format_change(score_change)
        rank_change_fmt = self._format_change(rank_change)

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

    @staticmethod
    def _format_change(text: str) -> str:
        """格式化变化值，确保有正负号"""
        if not text:
            return ""
        if text.startswith(("+", "-")):
            return text
        return f"+{text}"
