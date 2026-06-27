from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.custom_action import CustomAction
from maa.context import Context
from maa.define import RectType
from maa.pipeline import JRecognitionType, JOCR, JTemplateMatch, JActionType, JClick

from typing import Optional, Union
import json
from utils.logger import logger
from utils.params import parse_params


# 资源收集关卡边框配置（按资源类型分类）
RESOURCE_STAGES = {
    "特别军费行动": {
        1: [26, 475, 184, 56],
        2: [516, 523, 185, 56],
        3: [1005, 476, 185, 56],
        4: [315, 532, 57, 42],
        5: [803, 481, 55, 44],
    },
    "作战体能训练": {
        1: [26, 475, 184, 56],
        2: [516, 523, 185, 56],
        3: [1005, 476, 185, 56],
        4: [315, 532, 57, 42],
        5: [803, 481, 55, 44],
    },
    "兵种能力评级": {
        1: [164, 481, 62, 44],
        2: [516, 523, 185, 56],
        3: [1005, 476, 185, 56],
        4: [315, 532, 57, 42],
        5: [803, 481, 55, 44],
    },
    "载具对抗演练": {
        1: [170, 482, 50, 42],
        2: [660, 532, 50, 42],
        3: [1149, 484, 50, 42],
        4: [317, 530, 50, 42],
        5: [807, 483, 50, 42],
    },
}

# 次数显示区域ROI
COUNT_ROI = [903, 441, 27, 43]
# 加号按钮位置
PLUS_BUTTON = (1086, 470)
# 减号按钮位置
MINUS_BUTTON = (739, 470)
# 最大按钮模板
MAX_BUTTON_TEMPLATE = "farm_resources/max_count.png"


@AgentServer.custom_recognition("CheckResourceStage")
class CheckResourceStage(CustomRecognition):
    """检测资源收集关卡"""

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> Union[CustomRecognition.AnalyzeResult, Optional[RectType]]:
        # 获取参数
        params = parse_params(argv.custom_recognition_param)

        stage_name = params.get("stage_name", "")
        stage_index = params.get("stage_index", 1)
        resource_type = params.get("resource_type", "")
        lock_template = params.get("lock_template", "farm_resources/lock_icon.png")
        lock_threshold = params.get("lock_threshold", 0.7)

        # 根据资源类型和关卡编号获取ROI
        if resource_type and resource_type in RESOURCE_STAGES:
            type_stages = RESOURCE_STAGES[resource_type]
        else:
            type_stages = list(RESOURCE_STAGES.values())[0]

        if stage_index not in type_stages:
            logger.warning(f"关卡 {stage_index} 不在 {resource_type} 中")
            return None
        stage_roi = type_stages[stage_index]

        # OCR识别目标关卡（同时匹配带横杠和不带横杠的格式）
        stage_name_no_dash = stage_name.replace("-", "")
        ocr_detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(expected=[stage_name, stage_name_no_dash], roi=stage_roi),
            argv.image,
        )

        if not ocr_detail or not ocr_detail.box:
            return None

        # 检查高级账号标志干扰
        if hasattr(ocr_detail, 'text') and '奖励' in ocr_detail.text:
            x, y, w, h = stage_roi
            adjusted_roi = [x, y, int(w * 0.7), h]
            ocr_detail = context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(expected=[stage_name, stage_name_no_dash], roi=adjusted_roi),
                argv.image,
            )
            if not ocr_detail or not ocr_detail.box:
                return None

        # 检查锁定图标
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
                    logger.warning(f"[资源刷取] {stage_name}关卡被锁定")
                    return None
        except Exception:
            pass

        logger.info(f"[资源刷取] 找到关卡 {stage_name}，位置: {ocr_detail.box}")
        return CustomRecognition.AnalyzeResult(box=ocr_detail.box, detail="found")


@AgentServer.custom_action("SetBattleCount")
class SetBattleCount(CustomAction):
    """
    设置战斗次数

    参数：
    - target_count: 目标次数（1-6 或 "max"）
    - count_roi: 次数显示区域 [x, y, w, h]
    - plus_button: 加号按钮位置 [x, y]
    - max_template: 最大按钮模板路径
    """

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        # 获取参数
        params = parse_params(argv.custom_action_param)

        target_count = params.get("target_count", 1)
        count_roi = params.get("count_roi", COUNT_ROI)
        plus_x, plus_y = params.get("plus_button", PLUS_BUTTON)
        max_template = params.get("max_template", MAX_BUTTON_TEMPLATE)

        logger.info(f"[SetBattleCount] 参数: target_count={target_count}, type={type(target_count)}")

        # 获取当前截图
        image = context.tasker.controller.cached_image

        # 如果是最大，点击最大按钮
        if target_count == "max":
            max_detail = context.run_recognition_direct(
                JRecognitionType.TemplateMatch,
                JTemplateMatch(template=max_template, threshold=0.8),
                image,
            )
            if max_detail and max_detail.box:
                context.run_action_direct(
                    JActionType.Click,
                    JClick(),
                    max_detail.box,
                    "",
                )
            return CustomAction.RunResult(success=True)

        # OCR识别当前次数
        ocr_detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(expected=["1", "2", "3", "4", "5", "6"], roi=count_roi),
            image,
        )

        current_count = 1
        if ocr_detail and ocr_detail.hit and ocr_detail.all_results:
            try:
                current_count = int(ocr_detail.all_results[0].text.strip())
            except ValueError:
                current_count = 1

        # 计算需要点击的次数
        clicks_needed = target_count - current_count

        if clicks_needed > 0:
            # 点击加号增加次数
            for _ in range(clicks_needed):
                context.run_action_direct(
                    JActionType.Click,
                    JClick(),
                    (plus_x, plus_y, 10, 10),
                    "",
                )
        elif clicks_needed < 0:
            # 需要减少次数，先点击最大，再点击加号到目标次数
            context.run_action_direct(
                JActionType.Click,
                JClick(target=(0, 0, 0, 0)),
                (0, 0, 0, 0),
                "",
            )
            # 重新识别当前次数
            ocr_detail = context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(expected=["1", "2", "3", "4", "5", "6"], roi=count_roi),
                image,
            )
            if ocr_detail and ocr_detail.hit and ocr_detail.all_results:
                try:
                    current_count = int(ocr_detail.all_results[0].text.strip())
                except ValueError:
                    current_count = 1
            clicks_needed = target_count - current_count
            for _ in range(clicks_needed):
                context.run_action_direct(
                    JActionType.Click,
                    JClick(target=(plus_x, plus_y, 0, 0)),
                    (0, 0, 0, 0),
                    "",
                )

        return CustomAction.RunResult(success=True)


# 全局变量记录当前目标次数
_current_target_count = 6


@AgentServer.custom_action("ReduceBattleCount")
class ReduceBattleCount(CustomAction):
    """
    减少战斗次数（动态计算目标次数）

    参数：
    - minus_button: 减号按钮位置 [x, y]
    - count_roi: 次数显示区域 [x, y, w, h]
    """

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        global _current_target_count
        try:
            # 获取参数
            params = parse_params(argv.custom_action_param)

            minus_x, minus_y = params.get("minus_button", MINUS_BUTTON)
            count_roi = params.get("count_roi", COUNT_ROI)

            # OCR识别当前次数
            image = context.tasker.controller.cached_image
            ocr_detail = context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(expected=["1", "2", "3", "4", "5", "6"], roi=count_roi),
                image,
            )

            current_count = -1
            if ocr_detail and ocr_detail.hit and ocr_detail.all_results:
                try:
                    current_count = int(ocr_detail.all_results[0].text.strip())
                except ValueError:
                    current_count = -1

            # 减少目标次数（每次减少1）
            _current_target_count -= 1
            logger.info(f"[ReduceBattleCount] 当前次数: {current_count}, 新目标次数: {_current_target_count}")

            # 如果目标次数已经小于1，返回失败
            if _current_target_count < 1:
                logger.warning(f"[ReduceBattleCount] 目标次数已到最小，无法继续")
                _current_target_count = 6  # 重置
                return CustomAction.RunResult(success=False)

            # 点击减号按钮1次
            logger.info(f"[ReduceBattleCount] 点击减号按钮")
            context.run_action_direct(
                JActionType.Click,
                JClick(),
                (minus_x, minus_y, 10, 10),
                "",
            )

            return CustomAction.RunResult(success=True)
        except Exception as e:
            logger.error(f"[ReduceBattleCount] 执行异常: {e}")
            _current_target_count = 6  # 重置
            return CustomAction.RunResult(success=False)


@AgentServer.custom_action("ResetBattleCountTarget")
class ResetBattleCountTarget(CustomAction):
    """
    重置目标次数为6（调用ReduceBattleCount前需要调用）
    """

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        global _current_target_count
        _current_target_count = 6
        logger.info(f"[ResetBattleCountTarget] 目标次数重置为: {_current_target_count}")
        return CustomAction.RunResult(success=True)
