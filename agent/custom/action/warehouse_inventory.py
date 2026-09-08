from __future__ import annotations

import json
import re
import time
from collections import Counter
from typing import Any

import numpy as np
from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction
from maa.define import OCRResult
from maa.pipeline import JOCR, JRecognitionType, JTemplateMatch
from utils.logger import logger
from utils.maa_types import all_results_as, best_box
from utils.runtime_paths import get_runtime_paths

# 目标材料清单：中文名 -> 模板相对路径（相对 image/ 目录）。
# 补充模板只需在此登记并放置对应模板图，扫描即自动覆盖。
_MATERIALS: dict[str, str] = {
    "第二版能元": "warehouse/第二版能元.png",
    "训练用器材": "warehouse/训练用器材.png",
    "低级考核材料自选包": "warehouse/低级考核材料自选包.png",
    "中级考核材料自选包": "warehouse/中级考核材料自选包.png",
    "高级考核材料自选包": "warehouse/高级考核材料自选包.png",
    "基础技能材料自选包": "warehouse/基础技能材料自选包.png",
    "优秀毕业证书": "warehouse/优秀毕业证书.png",
}

# 仓库材料网格区域（1280x720 基准，实测 5 列 x 3 行，行中心 y=205/375/545）
_GRID_ROI = (30, 130, 800, 520)
# 模板阈值：自身匹配实测 0.95+，三个同款箱子互串 0.69~0.79，0.85 可干净区分
_TEMPLATE_THRESHOLD = 0.85

# 数量标签：OCR 实测标签中心 = 图标中心 + (+22, +76)（黑底白字，1~6 位数字）。
# 单个较大 ROI 覆盖滚动的 ±10px 纵向漂移，避免多候选重复 OCR 引入噪声。
_COUNT_ROI_DX = 20
_COUNT_ROI_DY = 52
_COUNT_ROI_W = 100
_COUNT_ROI_H = 40

# 滑动参数（1280x720 基准，列表中心 x=420）
_SCROLL_X = 420
_SCROLL_Y_TOP = 250
_SCROLL_Y_BOTTOM = 600
_SCROLL_DURATION_MS = 800
_SCROLL_SETTLE_SLEEP = 1.8

# 往返扫描：先滚回列表顶部，再 向下 5 屏 → 向上 5 屏 → 向下 5 屏。
# 每个材料至少被读到 2~3 次，用众数消除单次误读（参考 M9A WarehouseInventoryScan）。
_SCROLL_BACK_TO_TOP_PAGES = 6
_SEGMENT_PAGES = 5


def _parse_count(text: str) -> int | None:
    """从 OCR 文本中提取数量：取最长数字组（真实数量位数多于边缘噪声）。"""
    groups = re.findall(r"\d+", text.replace(",", ""))
    if not groups:
        return None
    return int(max(groups, key=len))


def _best_count(values: list[int]) -> int:
    """多次读数聚合：众数优先；无众数取最小（装饰条把数字读大时取最小可消除）。"""
    counter = Counter(values)
    most_common = counter.most_common()
    if len(most_common) > 1 and most_common[0][1] > most_common[1][1]:
        return most_common[0][0]
    return min(values)


@AgentServer.custom_action("WarehouseInventoryScan")
class WarehouseInventoryScan(CustomAction):
    """识别仓库中已配模板的目标材料数量，落盘 config/warehouse_inventory.json。

    扫描策略（参考 M9A WarehouseInventoryScan）：
    1. 先回到列表顶部；
    2. 每屏对全部目标材料做 TemplateMatch（阈值 0.85），命中后用固定偏移的
       OCR ROI 读取图标下方数量标签；
    3. 双向往返多屏扫描收集多次读数，用众数消除单次误读；
    4. 结果写入 config/warehouse_inventory.json（含数量、未找到标记与更新时间）。
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        try:
            return self._run(context, argv)
        except Exception:
            logger.exception("WarehouseInventoryScan 执行异常")
            return CustomAction.RunResult(success=False)

    def _run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        readings: dict[str, list[int]] = {name: [] for name in _MATERIALS}
        # 模板命中但数量 OCR 始终失败的材料：不能按 0 计（会误刷），跳过并提示
        unreadable: set[str] = set()

        logger.info("仓库扫描：滚回列表顶部")
        for _ in range(_SCROLL_BACK_TO_TOP_PAGES):
            context.tasker.controller.post_swipe(
                _SCROLL_X, _SCROLL_Y_BOTTOM, _SCROLL_X, _SCROLL_Y_TOP, _SCROLL_DURATION_MS
            ).wait()
            time.sleep(0.8)

        total_pages = _SEGMENT_PAGES * 3
        for page in range(total_pages):
            logger.info(f"仓库扫描第 {page + 1}/{total_pages} 屏")
            image = context.tasker.controller.post_screencap().wait().get()
            self._scan_page(context, image, readings, unreadable)
            # 三段方向：下 → 上 → 下（与 M9A 一致，往返覆盖）
            if page < _SEGMENT_PAGES:
                start_y, end_y = _SCROLL_Y_BOTTOM, _SCROLL_Y_TOP
            elif page < _SEGMENT_PAGES * 2:
                start_y, end_y = _SCROLL_Y_TOP, _SCROLL_Y_BOTTOM
            else:
                start_y, end_y = _SCROLL_Y_BOTTOM, _SCROLL_Y_TOP
            context.tasker.controller.post_swipe(
                _SCROLL_X, start_y, _SCROLL_X, end_y, _SCROLL_DURATION_MS
            ).wait()
            time.sleep(_SCROLL_SETTLE_SLEEP)

        counts: dict[str, int] = {}
        skipped: list[str] = []
        for name, values in readings.items():
            if not values:
                if name in unreadable:
                    # 命中但数量 OCR 失败：值未知，不能按 0 计（下游均衡刷取会误刷）
                    logger.warning(f"材料 {name} 数量识别不稳定，本轮跳过（不按 0 计）")
                    skipped.append(name)
                    continue
                # 未找到 ≠ 识别失败：模板在整轮扫描中从未命中，按 0 处理并在日志标记
                logger.warning(f"仓库中未找到材料 {name}，按 0 计")
                counts[name] = 0
                continue
            # 混入 0 的读数：真实数量为 0 时整轮都应是 0；0 更可能是标签
            # 部分进入 ROI 时被 OCR 误读的数字。剔除 0 后聚合。
            nonzero_values = [value for value in values if value > 0]
            if nonzero_values:
                values = nonzero_values
            counts[name] = _best_count(values)
            if len(set(values)) > 1:
                logger.warning(f"材料 {name} 多次读数不一致 {values}，取 {counts[name]}")

        output: dict[str, Any] = {
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "counts": counts,
            "skipped": skipped,
            "materials": {name: {"template": template} for name, template in _MATERIALS.items()},
        }
        out_path = get_runtime_paths().project_root / "config" / "warehouse_inventory.json"
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(
                json.dumps(output, indent=4, ensure_ascii=False), encoding="utf-8"
            )
        except OSError as error:
            logger.error(f"写入仓库数量快照失败: {out_path}, {error}")
            return CustomAction.RunResult(success=False)

        summary = ", ".join(f"{name}x{counts[name]}" for name in _MATERIALS if name in counts)
        logger.info(f"仓库材料数量已保存到 {out_path}: {summary}")
        if skipped:
            logger.warning(f"本轮跳过（数量识别不稳定）: {skipped}")
        return CustomAction.RunResult(success=True)

    def _scan_page(
        self,
        context: Context,
        image: Any,
        readings: dict[str, list[int]],
        unreadable: set[str],
    ) -> None:
        """对当前屏截图：每个材料模板匹配一次，命中后读取数量 OCR。"""
        for name, template in _MATERIALS.items():
            detail = context.run_recognition_direct(
                JRecognitionType.TemplateMatch,
                JTemplateMatch(
                    template=[template],
                    roi=_GRID_ROI,
                    threshold=[_TEMPLATE_THRESHOLD],
                    green_mask=True,
                ),
                image,
            )
            box = best_box(detail)
            if box is None:
                continue
            # best_box 返回 [x, y, w, h]（list），与 M9A 用法一致
            count = self._read_count(context, box[0], box[1], image)
            logger.debug(f"{name} box={box} count={count}")
            if count is None:
                unreadable.add(name)
            else:
                readings[name].append(count)

    def _read_count(self, context: Context, box_x: int, box_y: int, image: Any) -> int | None:
        """在图标下方的大 ROI 内 OCR 数量标签，失败返回 None。

        数量标签有两种配色：黑底白字（绝大多数材料）与白字叠在彩色图标/选中
        黄圈上（高级材料）。先直读；直读失败时做灰度阈值化（白字保留、彩色底
        变黑）再试一次，避免低对比度数字被误读。
        """
        roi = (
            box_x + _COUNT_ROI_DX,
            box_y + _COUNT_ROI_DY,
            _COUNT_ROI_W,
            _COUNT_ROI_H,
        )
        value = self._ocr_count(context, image, roi)
        if value is not None:
            return value
        # 兜底：阈值化（转 3 通道 BGR，MaaFW OCR 不接受单通道）
        roi_x, roi_y, roi_w, roi_h = roi
        try:
            crop = image[roi_y : roi_y + roi_h, roi_x : roi_x + roi_w]
            gray = crop[:, :, :3].mean(axis=2) if crop.ndim == 3 else crop
            bw = (gray > 170).astype("uint8") * 255
            clean = np.stack([bw] * 3, axis=-1)
        except Exception:
            return None
        value = self._ocr_count(context, clean, (0, 0, roi_w, roi_h))
        if value is None:
            logger.warning(f"数量 OCR 失败 box=({box_x},{box_y})")
        return value

    def _ocr_count(self, context: Context, image: Any, roi: tuple[int, int, int, int]) -> int | None:
        """对指定 ROI 做一次 OCR 并提取数字；无数字返回 None。"""
        count_detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(expected=[], roi=(roi[0], roi[1], roi[2], roi[3])),
            image,
        )
        text = "".join(result.text or "" for result in all_results_as(count_detail, OCRResult))
        return _parse_count(text)
