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
"""

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
import json

from utils.logger import logger


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
        # 解析自定义参数
        try:
            argv_dict: dict = json.loads(argv.custom_action_param)
        except json.JSONDecodeError as e:
            logger.error(f"LogOCRResult 参数解析失败: {e}")
            return CustomAction.RunResult(success=False)

        if not argv_dict:
            logger.warning("LogOCRResult 参数为空")
            return CustomAction.RunResult(success=True)

        # 获取自定义参数
        action_key = argv_dict.get("action_key", "")
        recognition_name = argv_dict.get("recognition_name", "")
        return_text = argv_dict.get("return_text", "")
        click_target = argv_dict.get("click_target", [])

        # 获取 OCR 识别结果
        image = context.tasker.controller.post_screencap().wait().get()
        reco_result = context.run_recognition(recognition_name, image)

        # 处理 OCR 识别结果
        if reco_result and reco_result.hit:
            best_result = reco_result.best_result
            # 输出到 UI 界面
            logger.info(f"{return_text}: {best_result.text}")

            # 根据 action_key 执行不同的动作
            if action_key == "Click":
                self._handle_click(context, best_result, click_target)
            elif action_key == "":
                logger.debug(f"仅返回 OCR 数据，不执行动作")
            else:
                logger.warning(f"未知的 action_key: {action_key}")
        else:
            logger.warning(f"OCR 识别失败 - 任务名称: {recognition_name}")

        return CustomAction.RunResult(success=True)

    def _handle_click(self, context: Context, best_result, click_target: list):
        """处理点击动作"""
        if click_target:
            # 点击传入参数中的坐标位置
            box = click_target
            center_x = box[0] + box[2] // 2
            center_y = box[1] + box[3] // 2
            logger.debug(f"点击位置: ({center_x}, {center_y})")
            context.tasker.controller.post_click(center_x, center_y).wait()
        elif best_result:
            # 点击最佳识别结果的中心位置
            box = best_result.box
            center_x = box[0] + box[2] // 2
            center_y = box[1] + box[3] // 2
            logger.debug(f"点击位置: ({center_x}, {center_y})")
            context.tasker.controller.post_click(center_x, center_y).wait()
        else:
            logger.warning("没有识别到结果，无法执行点击")
