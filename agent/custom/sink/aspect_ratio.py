"""任务流水线开始前的分辨率前置检查。

MaaKEDR 所有 ROI / 坐标 / 模板图以 1280x720（16:9）为基准，若设备分辨率
比例不是 16:9，模板匹配和 OCR 会大面积失效。此 Sink 只在每次任务流水线最
开始（排队任务的第一个任务启动前）检查一次控制器实际分辨率，不符合则停止
任务并给出提示，避免"跑半天全是识别失败"。
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
    """任务流水线开始时检查一次设备分辨率是否为 16:9，不符合则停止任务。"""

    def __init__(self) -> None:
        #: 本次流水线是否已检查过分辨率
        self._checked = False

    def on_tasker_task(
        self,
        tasker: Tasker,
        noti_type: NotificationType,
        detail: TaskerEventSink.TaskerTaskDetail,
    ) -> None:
        # 只在任务开始时处理
        if noti_type != NotificationType.Starting:
            return

        # MaaTaskerPostStop 标记上一次流水线结束，重置标记使下一次运行重新检查
        if detail.entry == "MaaTaskerPostStop":
            self._checked = False
            return

        # 分辨率检查只在流水线最开始进行一次，后续任务直接跳过
        if self._checked:
            return
        self._checked = True

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
            "🚨 分辨率比例不是 16:9，任务已停止！当前 {}x{}（比例 {:.4f}），请调整为: {}",
            width,
            height,
            actual_ratio,
            RECOMMENDED_RESOLUTIONS,
        )
        tasker.post_stop()
