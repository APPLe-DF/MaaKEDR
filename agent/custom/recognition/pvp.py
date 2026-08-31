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

        try:
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
        except Exception:
            # ctypes 回调中未捕获的异常会被 MaaFW 静默吞掉并误判为成功，
            # 这里显式捕获并返回 None（识别失败），让节点按未命中/超时处理。
            logger.exception("SelectPVPOpponent: analyze 异常，按识别失败处理")
            return None


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

        try:
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

            # 高账失败保护交叉校验：分数变化区域 OCR 为空 且 结果文案含「败」字才判定为保护。
            # 实机存在「分数不变但排名仍下降」的正常战斗，因此不能再要求排名也无变化；
            # 同时必须用「败」字交叉校验，避免分数变化未识别（OCR 漏检）被误判为
            # 「本场不扣分」的保护结论。
            protected = (not score_change_fmt) and ("败" in result_text)

            if protected:
                result_msg = f"高账失败保护触发：本场不扣分，积分:{current_score or '-'} 排名:{current_rank or '-'}"
            elif not score_change_fmt:
                # 分数变化未识别且结果并非失败：不能断言「本场不扣分」，如实输出未识别。
                result_msg = (
                    f"{result_text} 积分:{current_score or '-'}(变化值未识别) "
                    f"排名:{current_rank or '-'}({rank_change_fmt or '-'})"
                )
            else:
                result_msg = (
                    f"{result_text} 积分:{current_score}({score_change_fmt}) 排名:{current_rank}({rank_change_fmt})"
                )

            # 每次识别成功直接输出结果文案，不再预写 PVP.ExitResult 的 focus：
            # override_pipeline 的 focus 会跨识别周期残留，多场循环中某场识别失败时
            # 会重复打印上一场的文案；改为识别器内直接打印，随识别命中即时输出。
            logger.info("[PVP] {}", result_msg)

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
        except Exception:
            # ctypes 回调中未捕获的异常会被 MaaFW 静默吞掉并误判为成功，
            # 这里显式捕获并返回 None（识别失败），让节点按未命中/超时处理。
            logger.exception("ReadPVPResult: analyze 异常，按识别失败处理")
            return None

    @staticmethod
    def _format_change(text: str) -> str:
        """格式化变化值，确保有正负号"""
        if not text:
            return ""
        if text.startswith(("+", "-")):
            return text
        return f"+{text}"
