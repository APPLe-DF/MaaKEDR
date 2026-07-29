from __future__ import annotations

from typing import Any

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_recognition import CustomRecognition
from maa.define import RectType
from maa.pipeline import JOCR, JRecognitionType, JTemplateMatch
from utils.logger import logger
from utils.maa_types import ocr_text
from utils.params import parse_params

RESOURCE_STAGES = {
    "特别军费行动": {
        1: [170, 482, 50, 42],
        2: [660, 532, 50, 42],
        3: [1149, 484, 50, 42],
        4: [317, 530, 50, 42],
        5: [807, 483, 50, 42],
    },
    "作战体能训练": {
        1: [170, 482, 50, 42],
        2: [660, 532, 50, 42],
        3: [1149, 484, 50, 42],
        4: [317, 530, 50, 42],
    },
    "兵种能力评级": {
        1: [170, 482, 50, 42],
        2: [660, 532, 50, 42],
        3: [1149, 484, 50, 42],
        4: [317, 530, 50, 42],
    },
    "载具对抗演练": {
        1: [170, 482, 50, 42],
        2: [660, 532, 50, 42],
        3: [1149, 484, 50, 42],
        4: [317, 530, 50, 42],
        5: [807, 483, 50, 42],
    },
}


def _stage_roi_tuple(roi: list[int]) -> tuple[int, int, int, int] | None:
    """将 stage_roi 列表转换为 (x, y, w, h) 元组，长度不足时返回 None。"""
    if len(roi) >= 4:
        return roi[0], roi[1], roi[2], roi[3]
    logger.warning("CheckResourceStage: stage_roi 长度不足 4: {}", roi)
    return None


@AgentServer.custom_recognition("CheckResourceStage")
class CheckResourceStage(CustomRecognition):
    """检测资源收集关卡"""

    def _check_locked(
        self,
        context: Context,
        image: Any,
        stage_roi: list[int],
        lock_template: str,
        lock_threshold: float,
    ) -> bool:
        """在关卡识别区域内检测锁定图标"""
        if not lock_template:
            return False
        roi_tuple = _stage_roi_tuple(stage_roi)
        if roi_tuple is None:
            return False
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
                return True
        except Exception:
            return False
        return False

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        try:
            params = parse_params(argv.custom_recognition_param)
        except ValueError as error:
            logger.error("CheckResourceStage: {}", error)
            return None

        stage_name = params.get("stage_name", "")
        stage_index = params.get("stage_index", 1)
        resource_type = params.get("resource_type", "")
        lock_template = params.get("lock_template", "farm_resources/lock_icon.png")
        lock_threshold = params.get("lock_threshold", 0.7)

        if resource_type and resource_type in RESOURCE_STAGES:
            type_stages = RESOURCE_STAGES[resource_type]
        else:
            type_stages = list(RESOURCE_STAGES.values())[0]

        if stage_index not in type_stages:
            logger.warning("关卡 {} 不在 {} 中", stage_index, resource_type)
            return None
        stage_roi = type_stages[stage_index]
        roi_tuple = _stage_roi_tuple(stage_roi)
        if roi_tuple is None:
            return None

        image = argv.image

        if stage_index > 1 and self._check_locked(context, image, stage_roi, lock_template, lock_threshold):
            logger.warning("[资源刷取] {} 关卡被锁定", stage_name)
            context.override_next(argv.node_name, ["FarmResources.StageLocked"])
            return CustomRecognition.AnalyzeResult(box=(0, 0, 1, 1), detail={"status": "locked"})

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
            return None

        if "奖励" in ocr_text(ocr_detail):
            x, y, w, h = roi_tuple
            adjusted_roi = (x, y, int(w * 0.7), h)
            ocr_detail = context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(
                    expected=[stage_name, stage_name_no_dash],
                    roi=adjusted_roi,
                ),
                image,
            )
            if not ocr_detail or not ocr_detail.box:
                return None

        logger.info("[资源刷取] 找到关卡 {}，位置: {}", stage_name, ocr_detail.box)
        return CustomRecognition.AnalyzeResult(box=ocr_detail.box, detail={"status": "found"})
