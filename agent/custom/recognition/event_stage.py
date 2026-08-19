from __future__ import annotations

from typing import Any

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_recognition import CustomRecognition
from maa.define import RectType
from maa.pipeline import JOCR, JRecognitionType, JTemplateMatch
from utils.logger import logger
from utils.params import coerce_roi, parse_params


@AgentServer.custom_recognition("CheckAllSoldOut")
class CheckAllSoldOut(CustomRecognition):
    """Detect the shop's all-sold-out layout from multiple OCR hits."""

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        try:
            params = parse_params(argv.custom_recognition_param)
        except ValueError as error:
            logger.error("CheckAllSoldOut: {}", error)
            return None

        roi = coerce_roi(params.get("roi"), [0, 180, 1280, 540], "CheckAllSoldOut")
        detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(expected=["已售罄"], roi=(roi[0], roi[1], roi[2], roi[3])),
            argv.image,
        )
        results = getattr(detail, "all_results", None) if detail else None
        if not results or len(results) < 2:
            return None

        first_box = getattr(results[0], "box", None) or getattr(detail, "box", None)
        if not first_box:
            return None
        logger.info("[活动商店] 检测到全部商品售罄（{} 个标记）", len(results))
        return CustomRecognition.AnalyzeResult(box=first_box, detail={"status": "all_sold_out", "count": len(results)})


@AgentServer.custom_recognition("CheckEventStage")
class CheckEventStage(CustomRecognition):
    """检测活动关卡（按参数传入关卡名与识别区域，OCR 定位）"""

    def _stage_roi_or_none(self, stage_roi: list[int]) -> tuple[int, int, int, int] | None:
        result = coerce_roi(stage_roi, [-1, -1, -1, -1], "CheckEventStage")
        if result == [-1, -1, -1, -1]:
            return None
        return result[0], result[1], result[2], result[3]

    def _check_locked(
        self,
        context: Context,
        image: Any,
        stage_roi: list[int],
        lock_template: str,
        lock_threshold: float,
    ) -> tuple[int, int, int, int] | None:
        if not lock_template:
            return None
        roi_tuple = self._stage_roi_or_none(stage_roi)
        if roi_tuple is None:
            return None
        try:
            lock_detail = context.run_recognition_direct(
                JRecognitionType.TemplateMatch,
                JTemplateMatch(
                    template=[lock_template],
                    roi=roi_tuple,
                    threshold=[lock_threshold],
                ),
                image,
            )
            if lock_detail and lock_detail.box:
                box = lock_detail.box
                return (int(box[0]), int(box[1]), int(box[2]), int(box[3]))
        except Exception:
            return None
        return None

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        try:
            params = parse_params(argv.custom_recognition_param)
        except ValueError as error:
            logger.error("CheckEventStage: {}", error)
            return None

        stage_name = params.get("stage_name", "")
        stage_roi = coerce_roi(params.get("stage_roi"), [0, 0, 1280, 640], "CheckEventStage")
        lock_template = params.get("lock_template", "")
        lock_threshold = params.get("lock_threshold", 0.7)

        if not stage_name:
            logger.error("CheckEventStage: stage_name 为空")
            return None

        roi_tuple = self._stage_roi_or_none(stage_roi)
        if roi_tuple is None:
            return None

        image = argv.image

        lock_box = None
        if lock_template:
            lock_box = self._check_locked(context, image, stage_roi, lock_template, lock_threshold)
        if lock_box is not None:
            logger.warning("[活动刷取] {} 关卡被锁定", stage_name)
            context.override_next(argv.node_name, ["EventStage.StageLocked"])
            return CustomRecognition.AnalyzeResult(box=lock_box, detail={"status": "locked"})

        stage_name_no_dash = stage_name.replace("-", "")
        ocr_detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(
                expected=[stage_name, stage_name_no_dash],
                roi=roi_tuple,
            ),
            image,
        )

        if not ocr_detail or not ocr_detail.box:
            # 目标关卡不在当前视野：路由到向右滑动，滑完回来再找（EX4-1 在最右需滑到底）
            context.override_next(argv.node_name, ["EventStage.DragFindStage"])
            logger.info("[活动刷取] 未找到关卡 {}，向右滑动地图", stage_name)
            return CustomRecognition.AnalyzeResult(box=(400, 300, 1, 1), detail={"status": "not_found"})

        # 找到目标：显式恢复路由到结果检查，避免之前滑动分支的 override 残留
        context.override_next(argv.node_name, ["EventStage.CheckStageEntryResult"])
        logger.info("[活动刷取] 找到关卡 {}，位置: {}", stage_name, ocr_detail.box)
        return CustomRecognition.AnalyzeResult(box=ocr_detail.box, detail={"status": "found"})
