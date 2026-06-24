from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from maa.define import RectType
from maa.pipeline import JRecognitionType, JOCR, JTemplateMatch, JActionType, JSwipe

from typing import Optional, Union
import json


# 资源收集关卡边框配置（需要根据实际情况调整）
RESOURCE_STAGES = {
    1: [26, 475, 184, 56],    # 第一个屏幕
    2: [516, 523, 185, 56],   # 第一个屏幕
    3: [1005, 476, 185, 56],  # 第一个屏幕
    4: [315, 532, 57, 42],    # 第二个屏幕（滑动后）
    5: [803, 481, 55, 44],    # 第二个屏幕（滑动后）
}


@AgentServer.custom_recognition("CheckResourceStage")
class CheckResourceStage(CustomRecognition):
    """
    检测资源收集关卡（支持动态ROI、滑动和锁定检测）

    参数：
    - stage_name: 目标关卡名称（如"1-1"、"1-2"等）
    - stage_index: 目标关卡编号（1-5）
    - lock_template: 锁定图标模板路径（默认"farm_resources/lock_icon.png"）
    - lock_threshold: 锁定图标匹配阈值（默认0.7）
    """

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> Union[CustomRecognition.AnalyzeResult, Optional[RectType]]:
        # 获取参数
        param_str = argv.custom_recognition_param or "{}"
        current = param_str
        while isinstance(current, str):
            try:
                current = json.loads(current)
            except json.JSONDecodeError:
                break
        params = current if isinstance(current, dict) else {}

        stage_name = params.get("stage_name", "")
        stage_index = params.get("stage_index", 1)
        lock_template = params.get("lock_template", "farm_resources/lock_icon.png")
        lock_threshold = params.get("lock_threshold", 0.7)

        # 1. 获取目标关卡的边框ROI
        if stage_index not in RESOURCE_STAGES:
            return None
        stage_roi = RESOURCE_STAGES[stage_index]

        # 2. 如果目标关卡在第二个屏幕（4、5），先滑动（暂不实现，需要在pipeline中处理）
        # if stage_index >= 4:
        #     ...滑动逻辑...

        # 3. OCR识别目标关卡
        ocr_detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(expected=[stage_name], roi=stage_roi),
            argv.image,
        )

        if not ocr_detail or not ocr_detail.box:
            return None

        # 4. 检查是否有锁定图标
        try:
            if lock_template:
                x, y, w, h = ocr_detail.box
                lock_roi = [max(0, x - 20), max(0, y - 20), w + 40, h + 40]
                lock_detail = context.run_recognition_direct(
                    JRecognitionType.TemplateMatch,
                    JTemplateMatch(template=lock_template, roi=lock_roi, threshold=lock_threshold),
                    argv.image,
                )
                if lock_detail and lock_detail.box:
                    print(f"[CheckResourceStage] 关卡 {stage_name} 被锁定")
                    return None  # 被锁定，返回None让Pipeline处理
        except Exception as e:
            print(f"[CheckResourceStage] 锁定检测异常: {e}")

        # 5. 返回关卡位置
        print(f"[CheckResourceStage] 找到关卡 {stage_name}，位置: {ocr_detail.box}")
        return CustomRecognition.AnalyzeResult(box=ocr_detail.box, detail="found")
