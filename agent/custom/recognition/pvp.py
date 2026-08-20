from __future__ import annotations

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_recognition import CustomRecognition
from maa.define import RectType
from maa.pipeline import JOCR, JRecognitionType
from utils.logger import logger
from utils.maa_types import ocr_text
from utils.params import parse_params


@AgentServer.custom_recognition("SelectPVPOpponent")
class SelectPVPOpponent(CustomRecognition):
    """识别三个对手的等级，选择等级最低的进行点击"""

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        try:
            params = parse_params(argv.custom_recognition_param)
        except ValueError as error:
            logger.error("SelectPVPOpponent: {}", error)
            return None

        rois = params.get("rois", [])
        click_positions = params.get("click_positions", [])
        only_rec = params.get("only_rec", True)

        if len(rois) != 3 or len(click_positions) != 3:
            logger.error(
                "SelectPVPOpponent: 需要3个ROI和3个点击位置，得到 roi={} click={}",
                len(rois),
                len(click_positions),
            )
            return None

        image = argv.image

        best_value: float | None = None
        best_index: int = -1

        for i, roi in enumerate(rois):
            detail = context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(roi=roi, only_rec=only_rec),
                image,
            )
            text = ocr_text(detail)
            try:
                value = float(text)
                logger.info("[PVP] 对手{} 等级: {}", i + 1, value)
                if best_value is None or value < best_value:
                    best_value = value
                    best_index = i
            except (ValueError, TypeError):
                logger.warning("[PVP] 对手{} 无法识别等级: '{}'", i + 1, text)

        if best_index < 0:
            logger.error("SelectPVPOpponent: 未能识别任何对手的等级")
            return None

        click_x, click_y = click_positions[best_index]
        logger.info(
            "[PVP] 选择对手{} (等级最低: {}), 点击位置: [{}, {}]",
            best_index + 1,
            best_value,
            click_x,
            click_y,
        )

        return CustomRecognition.AnalyzeResult(
            box=[click_x, click_y, 10, 10],
            detail={
                "selected_index": best_index + 1,
                "selected_value": best_value,
            },
        )


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

        # 高级账号失败保护：分数与排名均不变，变化区域 OCR 为空
        protected = not score_change_fmt and not rank_change_fmt
        if protected:
            logger.info("[PVP] 未识别到分数与排名变化，疑似高级账号失败保护")
            result_msg = f"高账失败保护触发：本场不扣分，积分:{current_score or '-'} 排名:{current_rank or '-'}"
        else:
            result_msg = (
                f"{result_text} 积分:{current_score}({score_change_fmt}) 排名:{current_rank}({rank_change_fmt})"
            )
        logger.info("[PVP] {}", result_msg)

        context.override_pipeline(
            {
                "PVP.ExitResult": {
                    "focus": {
                        "Node.Action.Starting": {
                            "content": result_msg,
                            "display": ["log"],
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
                "protected": protected,
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
