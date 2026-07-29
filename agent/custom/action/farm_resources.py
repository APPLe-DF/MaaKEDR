from __future__ import annotations

from typing import Any

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import RecognitionDetail
from maa.pipeline import JOCR, JActionType, JClick, JRecognitionType, JTemplateMatch
from utils.logger import logger
from utils.maa_types import ocr_results
from utils.params import (
    coerce_point,
    coerce_roi,
    is_int_value,
    parse_params,
)

# agent 进程由 MaaFW 按任务逐次启动，进程内仅存在单一 tasker；
# 此模块级变量天然限定在单次任务生命周期内，无跨任务干扰风险。
_target: int | None = None

COUNT_ROI = [903, 441, 27, 43]
PLUS_BUTTON = (1086, 470)
MINUS_BUTTON = (739, 470)
MAX_BUTTON_TEMPLATE = "farm_resources/max_count.png"

_DEFAULT_TARGET = 6
_COUNT_EXPECTED = ["1", "2", "3", "4", "5", "6"]
_COUNT_MIN = 1
_COUNT_MAX = 6
_MAX_TEMPLATE_THRESHOLD: list[float] = [0.8, 0.8, 0.8]


def _read_battle_count(context: Context, count_roi: list[int], default: int) -> int:
    """OCR 识别当前战斗次数，失败时返回 default。"""
    image = context.tasker.controller.cached_image
    effective_roi = COUNT_ROI if len(count_roi) < 4 else count_roi
    x, y, w, h = effective_roi[0], effective_roi[1], effective_roi[2], effective_roi[3]
    ocr_detail: RecognitionDetail | None = context.run_recognition_direct(
        JRecognitionType.OCR,
        JOCR(expected=_COUNT_EXPECTED, roi=(x, y, w, h)),
        image,
    )
    if ocr_detail and ocr_detail.hit:
        results = ocr_results(ocr_detail)
        if results:
            try:
                return int(results[0].text.strip())
            except ValueError:
                pass
    return default


def _click_button(context: Context, x: int, y: int) -> None:
    """在指定坐标执行一次点击动作。"""
    context.run_action_direct(
        JActionType.Click,
        JClick(),
        (x, y, 10, 10),
        "",
    )


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

    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            params = parse_params(argv.custom_action_param, "target_count")
        except ValueError as error:
            logger.error("SetBattleCount: {}", error)
            return CustomAction.RunResult(success=False)

        target_count: Any = params["target_count"]
        count_roi = coerce_roi(params.get("count_roi", COUNT_ROI), COUNT_ROI, "SetBattleCount")
        plus_x, plus_y = coerce_point(
            params.get("plus_button", PLUS_BUTTON), PLUS_BUTTON, "SetBattleCount", "plus_button"
        )
        max_template = params.get("max_template", MAX_BUTTON_TEMPLATE)
        if not isinstance(max_template, str) or not max_template:
            logger.warning(
                "SetBattleCount: max_template 配置无效: type={}, value={}，回退到默认值 {}",
                type(max_template).__name__,
                max_template,
                MAX_BUTTON_TEMPLATE,
            )
            max_template = MAX_BUTTON_TEMPLATE

        logger.info("[SetBattleCount] 参数: target_count={}, type={}", target_count, type(target_count))

        image = context.tasker.controller.cached_image

        if target_count == "max":
            max_detail = context.run_recognition_direct(
                JRecognitionType.TemplateMatch,
                JTemplateMatch(template=[max_template], threshold=_MAX_TEMPLATE_THRESHOLD),
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

        if not is_int_value(target_count):
            try:
                target_count = int(target_count)  # type: ignore[arg-type]
                logger.info("[SetBattleCount] target_count 由非整数值转换为整数: {}", target_count)
            except (TypeError, ValueError):
                logger.error(
                    "[SetBattleCount] target_count 必须是 {}-{} 的整数或 'max'，得到: type={}, value={}",
                    _COUNT_MIN,
                    _COUNT_MAX,
                    type(target_count).__name__,
                    target_count,
                )
                return CustomAction.RunResult(success=False)

        if target_count < _COUNT_MIN:
            logger.warning(
                "[SetBattleCount] target_count < {}，已修正为 {}，原始值: {}",
                _COUNT_MIN,
                _COUNT_MIN,
                target_count,
            )
            target_count = _COUNT_MIN
        elif target_count > _COUNT_MAX:
            logger.warning(
                "[SetBattleCount] target_count > {}，已修正为 {}，原始值: {}",
                _COUNT_MAX,
                _COUNT_MAX,
                target_count,
            )
            target_count = _COUNT_MAX

        current_count = _read_battle_count(context, count_roi, default=_COUNT_MIN)
        clicks_needed = target_count - current_count

        if clicks_needed > 0:
            for _ in range(clicks_needed):
                _click_button(context, plus_x, plus_y)
        elif clicks_needed < 0:
            minus_x, minus_y = coerce_point(
                params.get("minus_button", MINUS_BUTTON), MINUS_BUTTON, "SetBattleCount", "minus_button"
            )
            logger.info(
                "[SetBattleCount] 当前次数 {} > 目标 {}，点击减号 {} 次",
                current_count,
                target_count,
                abs(clicks_needed),
            )
            for _ in range(abs(clicks_needed)):
                _click_button(context, minus_x, minus_y)

        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("ReduceBattleCount")
class ReduceBattleCount(CustomAction):
    """
    减少战斗次数（动态计算目标次数）

    参数：
    - minus_button: 减号按钮位置 [x, y]
    - count_roi: 次数显示区域 [x, y, w, h]
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        try:
            params = parse_params(argv.custom_action_param)
        except ValueError as error:
            logger.error("ReduceBattleCount: {}", error)
            return CustomAction.RunResult(success=False)

        try:
            minus_x, minus_y = coerce_point(
                params.get("minus_button", MINUS_BUTTON), MINUS_BUTTON, "ReduceBattleCount", "minus_button"
            )
            count_roi = coerce_roi(params.get("count_roi", COUNT_ROI), COUNT_ROI, "ReduceBattleCount")

            global _target
            target: Any = _target if _target is not None else _DEFAULT_TARGET
            if not is_int_value(target):
                target = _DEFAULT_TARGET
                logger.info("[ReduceBattleCount] target 未初始化，自动设为 {}", _DEFAULT_TARGET)

            if target <= _COUNT_MIN:
                logger.warning(
                    "[ReduceBattleCount] 目标次数已到最小({}≤{})，无法继续",
                    target,
                    _COUNT_MIN,
                )
                return CustomAction.RunResult(success=False)

            target -= 1
            _target = target

            current_count = _read_battle_count(context, count_roi, default=-1)

            logger.info(
                "[ReduceBattleCount] 当前次数: {}, 新目标次数: {}",
                current_count,
                target,
            )

            logger.info("[ReduceBattleCount] 点击减号按钮")
            _click_button(context, minus_x, minus_y)

            return CustomAction.RunResult(success=True)
        except Exception:
            logger.exception("[ReduceBattleCount] 执行异常")
            return CustomAction.RunResult(success=False)


@AgentServer.custom_action("ResetBattleCountTarget")
class ResetBattleCountTarget(CustomAction):
    """
    重置目标次数为 _DEFAULT_TARGET（调用 ReduceBattleCount 前需要调用）
    """

    def run(self, context: Context, argv: CustomAction.RunArg) -> CustomAction.RunResult:
        global _target
        _target = _DEFAULT_TARGET
        logger.info("[ResetBattleCountTarget] 目标次数重置为: {}", _DEFAULT_TARGET)
        return CustomAction.RunResult(success=True)
