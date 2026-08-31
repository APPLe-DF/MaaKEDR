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

# 注意：该 agent 进程在 MaaFW 生命周期内常驻，会跨任务（含同一次队列中的多次刷取）
# 存活，模块级 _target 存在跨任务残留风险，不能假设“按任务逐次启动”。
# ReduceBattleCount 每次执行都会用 OCR 读到的屏幕当前次数重新校准 _target，
# 仅在 OCR 读取失败时回退到该跟踪值（有界单调递减，见 _next_target）。
# 每次进入关卡界面时由 SetBattleCount 调用 _reset_target 清零该值（见下），
# 使首次减次的 OCR 失败回退不会用到上一任务耗尽后的残留值（1）。
_target: int | None = None

COUNT_ROI = [903, 441, 27, 43]
PLUS_BUTTON = (1086, 470)
MINUS_BUTTON = (739, 470)
MAX_BUTTON_TEMPLATE = "farm_resources/max_count.png"
MAX_BUTTON_ROI = (1008, 476, 125, 109)

_DEFAULT_TARGET = 6
_COUNT_EXPECTED = ["1", "2", "3", "4", "5", "6"]
_COUNT_MIN = 1
_COUNT_MAX = 6
_MAX_TEMPLATE_THRESHOLD: list[float] = [0.8, 0.8, 0.8]


def _read_battle_count(context: Context, count_roi: list[int], default: int) -> int:
    """OCR 识别当前战斗次数，失败时返回 default。"""
    image = context.tasker.controller.cached_image
    roi = coerce_roi(count_roi, COUNT_ROI, "ReadBattleCount")
    ocr_detail: RecognitionDetail | None = context.run_recognition_direct(
        JRecognitionType.OCR,
        JOCR(expected=_COUNT_EXPECTED, roi=(roi[0], roi[1], roi[2], roi[3])),
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


def _next_target(current_count: int, tracked: int | None) -> int | None:
    """计算「再减少一次」后的目标次数；返回 None 表示已到最小（1），无法继续。

    - current_count >= 1：以屏幕实际次数为准（target = current_count - 1），
      并以此修正跨任务残留的 tracked 值。回归场景：同一次队列中的第二次
      「剩余体力刷取」进入关卡时次数已重置为 6，而 tracked 仍是上一轮耗尽
      后的 1，旧实现因此误判「已到最小」直接放弃，导致本轮一场未打。
    - current_count < 1：OCR 读取失败，回退到 tracked（有界单调递减），
      避免无法读取时盲点减号或无限循环。
    """
    if current_count >= _COUNT_MIN:
        if current_count <= _COUNT_MIN:
            return None
        return current_count - 1

    target = tracked if tracked is not None else _DEFAULT_TARGET
    if target <= _COUNT_MIN:
        return None
    return target - 1


def _reset_target() -> None:
    """重置跨任务残留的模块级跟踪值 _target。

    agent 进程在 MaaFW 生命周期内常驻，模块级 _target 会跨任务存活：
    上一任务清空体力结束后其值为 1，若本任务首次减次前不重置，一旦 OCR
    读取失败就会回退到该残留值，被误判「已到最小」返回失败，触发 on_error
    走 NoStamina 退出，导致本轮一场未打（与已修复的 ReduceBattleCount
    跨任务残留问题同源，见 5dbef88）。
    调用方 SetBattleCount 在两种刷取任务（资源刷取/剩余体力刷取）的任何模式下
    都先于首次减次执行，且不会出现在减次循环内部，是安全的任务入口重置点。
    """
    global _target
    _target = None


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

        # 进入关卡界面即视为新任务开始：清零跨任务残留的跟踪值，
        # 否则上一任务耗尽后的残留值（1）会在本任务首次减次 OCR 失败时
        # 被回退使用，导致误判「已到最小」提前退出（见 _reset_target）。
        _reset_target()

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

        logger.debug("[SetBattleCount] 参数: target_count={}, type={}", target_count, type(target_count))

        image = context.tasker.controller.cached_image

        if target_count == "max":
            max_detail = context.run_recognition_direct(
                JRecognitionType.TemplateMatch,
                JTemplateMatch(
                    template=[max_template],
                    threshold=_MAX_TEMPLATE_THRESHOLD,
                    roi=MAX_BUTTON_ROI,
                ),
                image,
            )
            if max_detail and max_detail.box:
                logger.debug("[SetBattleCount] 检测到最大按钮，点击设置最大次数: {}", max_detail.box)
                context.run_action_direct(
                    JActionType.Click,
                    JClick(),
                    max_detail.box,
                    "",
                )
            else:
                logger.warning(
                    "[SetBattleCount] 未检测到最大按钮模板 {} (threshold={})，保持当前次数不变",
                    max_template,
                    _MAX_TEMPLATE_THRESHOLD,
                )
            return CustomAction.RunResult(success=True)

        if not is_int_value(target_count):
            try:
                target_count = int(target_count)  # type: ignore[arg-type]
                logger.debug("[SetBattleCount] target_count 由非整数值转换为整数: {}", target_count)
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
            logger.debug(
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

    目标次数优先取自屏幕 OCR 的当前次数（每次只减 1），并随读数重新校准进程内
    跟踪值 _target；OCR 读取失败时才回退到跟踪值（有界递减）。返回失败表示已到
    最小次数（1），由管道 on_error 走 NoStamina 退出本次刷取。
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

            current_count = _read_battle_count(context, count_roi, default=-1)
            target = _next_target(current_count, _target)
            if target is None:
                logger.warning(
                    "[ReduceBattleCount] 无法继续减少：当前次数={}, 跟踪目标={}（已到最小 {}）",
                    current_count,
                    _target,
                    _COUNT_MIN,
                )
                return CustomAction.RunResult(success=False)

            _target = target

            logger.debug(
                "[ReduceBattleCount] 当前次数: {}, 新目标次数: {}",
                current_count,
                target,
            )

            logger.debug("[ReduceBattleCount] 点击减号按钮")
            _click_button(context, minus_x, minus_y)

            return CustomAction.RunResult(success=True)
        except Exception:
            logger.exception("[ReduceBattleCount] 执行异常")
            return CustomAction.RunResult(success=False)
