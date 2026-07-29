"""
OCR 结果日志输出模块

在 UI 日志界面上显示重要节点 OCR 识别结果，方便用户查看任务进度和结果。

用法示例：
{
    "NodeName": {
        "action": "Custom",
        "custom_action": "LogOCRResult",
        "custom_action_param": {
            "recognition_name": "OCR_NodeName",
            "action_key": "Click",
            "return_text": "识别结果",
            "click_target": [x, y, w, h]
        }
    }
}

参数说明：
- recognition_name: OCR 识别节点名称
- action_key: 动作类型（Click/""）
- return_text: 输出描述
- click_target: 点击坐标 [x, y, w, h]（可选，仅在 action_key=Click 时使用）
- fail_on_invalid_target: click_target 长度不足 4 时是否返回失败
  （True 返 success=False，False 仅 warning 跳过，默认 False）
"""

from __future__ import annotations

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import RecognitionResult
from utils.logger import logger
from utils.maa_types import has_box_result, ocr_text
from utils.params import parse_params


@AgentServer.custom_action("LogOCRResult")
class LogOCRResult(CustomAction):
    """
    自定义动作：OCR 结果日志输出

    在 UI 日志界面上显示重要节点 OCR 识别结果，方便用户查看任务进度和结果。
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        try:
            argv_dict = parse_params(argv.custom_action_param)
        except ValueError as error:
            logger.error("LogOCRResult: {}", error)
            return CustomAction.RunResult(success=False)

        if not argv_dict:
            logger.warning("LogOCRResult 参数为空，跳过执行")
            return CustomAction.RunResult(success=True)

        action_key = argv_dict.get("action_key", "")
        recognition_name = argv_dict.get("recognition_name", "")
        return_text = argv_dict.get("return_text", "")
        click_target = argv_dict.get("click_target", [])
        fail_on_invalid_target = bool(argv_dict.get("fail_on_invalid_target", False))

        image = context.tasker.controller.post_screencap().wait().get()
        reco_result = context.run_recognition(recognition_name, image)

        if reco_result and reco_result.hit:
            text = ocr_text(reco_result)
            if not text:
                return CustomAction.RunResult(success=True)
            logger.info("{}: {}", return_text, text)

            best_result = reco_result.best_result
            if action_key == "Click":
                click_ok = self._handle_click(context, best_result, click_target, fail_on_invalid_target)
                if not click_ok:
                    return CustomAction.RunResult(success=False)
            elif action_key == "":
                logger.debug("仅返回 OCR 数据，不执行动作")
            else:
                logger.warning("未知的 action_key: {}", action_key)
        else:
            logger.warning("OCR 识别失败 - 任务名称: {}", recognition_name)

        return CustomAction.RunResult(success=True)

    def _handle_click(
        self,
        context: Context,
        best_result: RecognitionResult | None,
        click_target: list[int],
        fail_on_invalid_target: bool = False,
    ) -> bool:
        """
        处理点击动作。

        Args:
            fail_on_invalid_target: click_target 元素不足 4 个时，
                True 返回 False（让 run 返回 success=False），
                False 仅 warning 并跳过点击（默认行为）。

        Returns:
            是否成功执行了点击动作。
        """
        if click_target:
            if len(click_target) < 4:
                logger.warning(
                    "click_target 需要 4 个元素 [x, y, w, h]，得到: {} (值: {})，跳过点击",
                    len(click_target),
                    click_target,
                )
                return not fail_on_invalid_target
            center_x = click_target[0] + click_target[2] // 2
            center_y = click_target[1] + click_target[3] // 2
            logger.debug("点击位置: ({}, {})", center_x, center_y)
            context.tasker.controller.post_click(center_x, center_y).wait()
            return True
        elif has_box_result(best_result):
            box = best_result.box
            center_x = box[0] + box[2] // 2
            center_y = box[1] + box[3] // 2
            logger.debug("点击位置: ({}, {})", center_x, center_y)
            context.tasker.controller.post_click(center_x, center_y).wait()
            return True
        else:
            logger.warning("没有识别到结果，无法执行点击")
            return False
