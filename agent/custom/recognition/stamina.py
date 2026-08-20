from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_recognition import CustomRecognition
from maa.define import RectType
from maa.pipeline import JOCR, JRecognitionType
from utils.logger import logger
from utils.maa_types import ocr_text
from utils.params import coerce_roi, parse_params

#: 雪松体力恢复速率：每恢复 1 点体力所需分钟数（实测：4 分钟/1 点）
STAMINA_RECOVER_MINUTES_PER_POINT = 4


def rotate_image(image: np.ndarray, angle_deg: float) -> np.ndarray:
    """以图像中心为轴旋转图像（逆时针为正），双线性插值，返回新画布图像。"""
    if image.ndim == 2:
        image = image[:, :, np.newaxis]
    h, w = image.shape[:2]
    rad = np.deg2rad(angle_deg)
    cos, sin = np.cos(rad), np.sin(rad)

    nw = max(int(abs(w * cos) + abs(h * sin)) + 1, 1)
    nh = max(int(abs(w * sin) + abs(h * cos)) + 1, 1)

    cx, cy = w / 2.0, h / 2.0
    ncx, ncy = nw / 2.0, nh / 2.0

    ys, xs = np.mgrid[0:nh, 0:nw].astype(np.float32)
    # 目标坐标 -> 源坐标（逆变换）
    src_x = cos * (xs - ncx) + sin * (ys - ncy) + cx
    src_y = -sin * (xs - ncx) + cos * (ys - ncy) + cy

    x0 = np.floor(src_x).astype(np.int32)
    y0 = np.floor(src_y).astype(np.int32)
    x1 = x0 + 1
    y1 = y0 + 1

    # 越界裁剪
    x0c = np.clip(x0, 0, w - 1)
    x1c = np.clip(x1, 0, w - 1)
    y0c = np.clip(y0, 0, h - 1)
    y1c = np.clip(y1, 0, h - 1)

    fx = (src_x - x0).astype(np.float32)[..., np.newaxis]
    fy = (src_y - y0).astype(np.float32)[..., np.newaxis]

    c00 = image[y0c, x0c].astype(np.float32)
    c10 = image[y0c, x1c].astype(np.float32)
    c01 = image[y1c, x0c].astype(np.float32)
    c11 = image[y1c, x1c].astype(np.float32)

    top = c00 * (1 - fx) + c10 * fx
    bottom = c01 * (1 - fx) + c11 * fx
    out = top * (1 - fy) + bottom * fy
    out = np.round(out).astype(image.dtype)

    if image.shape[2] == 1:
        out = out[:, :, 0]
    return out


def _first_int(text: str) -> int | None:
    """从 OCR 文本中提取第一个正整数；无则返回 None。"""
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


@AgentServer.custom_recognition("ReadStamina")
class ReadStamina(CustomRecognition):
    """读取雪松主界面体力数值（倾斜区域，OCR 前先旋转扶正）。

    为提升 OCR 稳定性，当前体力与体力上限分两个 ROI 各自识别（两者存在距离，
    合并识别易互相干扰）。
    """

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        try:
            params = parse_params(argv.custom_recognition_param)
        except ValueError as error:
            logger.error("ReadStamina: {}", error)
            return None

        current_roi = coerce_roi(params.get("current_roi", [0, 0, 0, 0]), [0, 0, 0, 0], "ReadStamina")
        cap_roi = coerce_roi(params.get("cap_roi", [0, 0, 0, 0]), [0, 0, 0, 0], "ReadStamina")
        #: 屏幕上数字的倾斜角；纠正角为 -tilt_angle（见 _read_number）
        tilt_angle = float(params.get("tilt_angle", params.get("rotate_angle", -45.0)))
        # 可选的上限兜底（cap_roi 读取失败时使用），强制数值化
        cap_fallback: int | None = None
        raw_cap = params.get("stamina_cap", None)
        if raw_cap is not None:
            try:
                cap_fallback = int(raw_cap)
            except (TypeError, ValueError):
                logger.warning(
                    "ReadStamina: stamina_cap 参数非整数（{}），忽略兜底", raw_cap
                )

        if current_roi == [0, 0, 0, 0] or cap_roi == [0, 0, 0, 0]:
            logger.warning("ReadStamina: 未配置 current_roi / cap_roi")
            return None

        image = argv.image
        current = self._read_number(context, image, current_roi, tilt_angle)
        cap = self._read_number(context, image, cap_roi, tilt_angle) or cap_fallback

        if current is None or not cap:
            logger.info("[雪松] 未识别到完整体力数值（当前: {}，上限: {}）, 跳过回满时间计算", current, cap)
            return None

        # 体力达到自然恢复上限后不再随时间增长，因此没有“回满时间”
        if current >= cap:
            if current > cap:
                logger.info("[雪松] 体力 {}/{}（已超出自然恢复上限，不再随时间恢复）", current, cap)
            else:
                logger.info("[雪松] 体力 {}/{}（已达自然恢复上限，不再随时间恢复）", current, cap)
            return CustomRecognition.AnalyzeResult(
                box=(current_roi[0], current_roi[1], current_roi[2], current_roi[3]),
                detail={"current": current, "cap": cap, "full": True},
            )

        missing = cap - current
        minutes = missing * float(STAMINA_RECOVER_MINUTES_PER_POINT)
        full_time = datetime.now() + timedelta(minutes=minutes)
        logger.info(
            "体力将在 {} 回满。({}h {}m 后)",
            full_time.strftime("%Y-%m-%d %H:%M"),
            int(minutes) // 60,
            int(minutes) % 60,
        )
        return CustomRecognition.AnalyzeResult(
            box=(current_roi[0], current_roi[1], current_roi[2], current_roi[3]),
            detail={
                "current": current,
                "cap": cap,
                "full": False,
                "minutes_to_full": int(minutes),
            },
        )

    def _read_number(
        self, context: Context, image: Any, roi: list[int], angle: float
    ) -> int | None:
        """单个 ROI：旋转扶正后 OCR，提取第一个整数。

        angle 为屏幕上数字的“倾斜角”（tilt_angle），纠正角取其相反数。
        """
        x, y, w, h = [max(0, int(v)) for v in roi]
        if w <= 0 or h <= 0:
            logger.warning("ReadStamina: ROI [{}] 宽或高非正，跳过 OCR", roi)
            return None
        if image.ndim != 3 or y + h > image.shape[0] or x + w > image.shape[1]:
            logger.warning("ReadStamina: ROI [{}] 超出截图范围", roi)
            return None

        sub = image[y : y + h, x : x + w]
        rotated = rotate_image(sub, -angle)

        try:
            detail = context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(roi=(0, 0, int(rotated.shape[1]), int(rotated.shape[0])), only_rec=True),
                rotated,
            )
        except Exception as exc:
            logger.warning("ReadStamina: OCR 失败: {}", exc)
            return None

        if not detail or not detail.box:
            return None
        return _first_int(ocr_text(detail))
