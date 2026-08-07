"""任务开始前的分辨率前置检查。

MaaKEDR 所有 ROI / 坐标 / 模板图以 1280x720（16:9）为基准，若设备分辨率
比例不是 16:9，模板匹配和 OCR 会大面积失效。此 Sink 在每次任务开始时检查
控制器实际分辨率，不符合则停止任务并给出提示，避免"跑半天全是识别失败"。
"""

from __future__ import annotations

from maa.agent.agent_server import AgentServer
from maa.event_sink import NotificationType
from maa.tasker import Tasker, TaskerEventSink
from utils import logger

#: 允许的宽高比误差（16:9 = 1.7778）
RATIO_TOLERANCE = 0.02

#: 推荐分辨率提示文案
RECOMMENDED_RESOLUTIONS = "2560x1440, 1920x1080, 1600x900, 1280x720(推荐)"


def is_aspect_ratio_16x9(width: int, height: int) -> bool:
    """判断分辨率是否为 16:9 比例（含容差）。"""
    if width <= 0 or height <= 0:
        return False
    return abs(width / height - 16 / 9) <= RATIO_TOLERANCE


@AgentServer.tasker_sink()
class AspectRatioChecker(TaskerEventSink):
    """任务开始时检查设备分辨率是否为 16:9，不符合则停止任务。"""

    def on_tasker_task(
        self,
        tasker: Tasker,
        noti_type: NotificationType,
        detail: TaskerEventSink.TaskerTaskDetail,
    ) -> None:
        # 只在任务开始时检查
        if noti_type != NotificationType.Starting:
            return

        # 忽略停止任务事件
        if detail.entry == "MaaTaskerPostStop":
            return

        controller = tasker.controller

        try:
            width, height = controller.resolution
        except Exception as exc:
            logger.warning("AspectRatioChecker: 获取分辨率失败: {}", exc)
            return

        width = int(width)
        height = int(height)
        if width <= 0 or height <= 0:
            logger.error("AspectRatioChecker: 分辨率无效: {}x{}", width, height)
            tasker.post_stop()
            return

        if is_aspect_ratio_16x9(width, height):
            logger.info("AspectRatioChecker: 分辨率检查通过: {}x{}", width, height)
            return

        actual_ratio = width / height
        logger.error(
            "🚨 分辨率比例不是 16:9，任务已停止！当前 {}x{}（比例 {:.4f}），"
            "请调整为: {}",
            width,
            height,
            actual_ratio,
            RECOMMENDED_RESOLUTIONS,
        )
        tasker.post_stop()
