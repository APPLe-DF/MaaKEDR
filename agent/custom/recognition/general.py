from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any, cast

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_recognition import CustomRecognition
from maa.define import RecognitionDetail, RectType
from maa.pipeline import (
    JOCR,
    JAnd,
    JColorMatch,
    JDirectHit,
    JFeatureMatch,
    JNeuralNetworkClassify,
    JNeuralNetworkDetect,
    JOr,
    JRecognitionParam,
    JRecognitionType,
    JTemplateMatch,
)
from utils.logger import logger
from utils.params import parse_params

#: 内联子识别类型名 → MaaFW 识别参数类型（与 pipeline 的 `recognition` 取值一致）。
#: 不支持 Custom：嵌套自定义识别在本识别内部再跑一次没有实际用途，且容易绕出无限递归。
RECOGNITION_PARAM_CLASSES: dict[str, Callable[..., JRecognitionParam]] = {
    "DirectHit": JDirectHit,
    "TemplateMatch": JTemplateMatch,
    "FeatureMatch": JFeatureMatch,
    "ColorMatch": JColorMatch,
    "OCR": JOCR,
    "NeuralNetworkClassify": JNeuralNetworkClassify,
    "NeuralNetworkDetect": JNeuralNetworkDetect,
    "And": JAnd,
    "Or": JOr,
}

#: 子识别的 scalars 写法归一化：pipeline 允许 `template: "a.png"` / `threshold: 0.8`，
#: 而 dataclass 里对应字段是列表，直接透传会让 `param_class(**data)` 抛 TypeError。
LIST_VALUED_FIELDS: dict[str, tuple[str, ...]] = {
    "TemplateMatch": ("template", "threshold"),
    "FeatureMatch": ("template",),
    "NeuralNetworkDetect": ("expected", "threshold"),
    "NeuralNetworkClassify": ("expected",),
    "OCR": ("expected",),
}


def _rect(value: Any) -> list[int] | None:
    """把 Rect / [x, y, w, h] / {"x": ...} 统一成 [x, y, w, h]，非法值返回 None。"""
    if value is None:
        return None
    if isinstance(value, dict):
        try:
            box = [int(value[key]) for key in ("x", "y", "w", "h")]
        except (KeyError, TypeError, ValueError):
            return None
    elif isinstance(value, list | tuple):
        if len(value) < 4:
            return None
        try:
            box = [int(item) for item in value[:4]]
        except (TypeError, ValueError):
            return None
    else:
        try:
            box = [int(value.x), int(value.y), int(value.w), int(value.h)]
        except (AttributeError, TypeError, ValueError):
            return None
    if box[2] <= 0 or box[3] <= 0:
        return None
    return box


def _intersection_area(a: list[int], b: list[int]) -> int:
    """两个 [x, y, w, h] 框的交集面积（无重叠为 0）。"""
    x0 = max(a[0], b[0])
    y0 = max(a[1], b[1])
    x1 = min(a[0] + a[2], b[0] + b[2])
    y1 = min(a[1] + a[3], b[1] + b[3])
    if x1 <= x0 or y1 <= y0:
        return 0
    return (x1 - x0) * (y1 - y0)


def _best_overlap(box: list[int], others: list[list[int]], min_overlap: float) -> list[int] | None:
    """在 others 里找与 box 重叠最多、且交集面积 ≥ min_overlap × box 面积的框。"""
    area = box[2] * box[3]
    best: list[int] | None = None
    best_area = 0
    for other in others:
        intersection = _intersection_area(box, other)
        if intersection <= 0 or intersection < area * min_overlap:
            continue
        if intersection > best_area:
            best, best_area = other, intersection
    return best


def _sort_candidates(
    candidates: list[list[list[int]]],
    order_by: str,
    box_from: int,
) -> list[list[list[int]]]:
    """按 order_by 排序候选（排序键取第 box_from 个子识别的框），返回新列表。"""
    key = order_by.lower()
    if key == "random":
        shuffled = list(candidates)
        random.shuffle(shuffled)
        return shuffled
    if key == "area":
        return sorted(candidates, key=lambda candidate: -(candidate[box_from][2] * candidate[box_from][3]))
    if key == "horizontal":
        return sorted(candidates, key=lambda candidate: (candidate[box_from][0], candidate[box_from][1]))
    # 其余一律按 Vertical：最靠上的优先，同一行从左到右
    return sorted(candidates, key=lambda candidate: (candidate[box_from][1], candidate[box_from][0]))


def _normalize_param_data(type_name: str, raw: dict[str, Any]) -> dict[str, Any]:
    """把 pipeline 里的标量写法补成 dataclass 需要的列表写法。"""
    data = dict(raw)
    for field in LIST_VALUED_FIELDS.get(type_name, ()):
        value = data.get(field)
        if isinstance(value, str):
            data[field] = [value]
        elif isinstance(value, int | float) and not isinstance(value, bool):
            data[field] = [float(value)]
        elif isinstance(value, list | tuple):
            data[field] = list(value)
    # OCR 的 threshold 是单个浮点数，不接受列表
    if type_name == "OCR":
        threshold = data.get("threshold")
        if isinstance(threshold, list | tuple) and len(threshold) == 1:
            data["threshold"] = float(threshold[0])
    template = data.get("template")
    if isinstance(template, str):
        data["template"] = [template]
    return data


def _build_recognition_param(type_name: str, raw: dict[str, Any]) -> JRecognitionParam | None:
    """把内联识别定义（`{"type": ..., "param": {...}}` 的 param）转成 MaaFW 参数对象。"""
    param_class = RECOGNITION_PARAM_CLASSES.get(type_name)
    if param_class is None:
        logger.warning("AllOfIntersect: 不支持的内联识别类型 {}", type_name)
        return None
    try:
        return param_class(**_normalize_param_data(type_name, raw))
    except TypeError as error:
        logger.error("AllOfIntersect: 构造 {} 参数失败（{}），原始参数 {}", type_name, error, raw)
        return None


def _run_sub(context: Context, image: Any, sub: Any) -> RecognitionDetail | None:
    """执行一个子识别；返回 RecognitionDetail（失败为 None）。

    字符串 → 直接跑已有节点（复用节点自己的参数与默认值）；
    对象 → `{"type": ..., "param": {...}}` 或节点体 `{"recognition": {...}}`，内联跑一次。
    """
    if isinstance(sub, str):
        return context.run_recognition(sub, image)
    if not isinstance(sub, dict):
        logger.warning("AllOfIntersect: 子识别定义非法（{}），已跳过", type(sub).__name__)
        return None

    node = sub.get("recognition") if "recognition" in sub else sub
    if not isinstance(node, dict):
        logger.warning("AllOfIntersect: 子识别节点体非法，已跳过")
        return None

    type_name = node.get("type")
    if not isinstance(type_name, str):
        logger.warning("AllOfIntersect: 子识别缺少 type 字段，已跳过")
        return None

    param = node.get("param")
    if not isinstance(param, dict):
        param = {key: value for key, value in node.items() if key not in ("type", "param")}
    jparam = _build_recognition_param(type_name, cast(dict[str, Any], param))
    if jparam is None:
        return None

    try:
        reco_type = JRecognitionType(type_name)
    except ValueError:
        logger.warning("AllOfIntersect: 未知识别类型 {}，已跳过", type_name)
        return None
    return context.run_recognition_direct(reco_type, jparam, image)


def _boxes(detail: RecognitionDetail | None) -> list[list[int]]:
    """识别详情 → [[x, y, w, h], ...]（取全部结果，退化为过滤后结果）。"""
    if detail is None or not detail.hit:
        return []
    boxes: list[list[int]] = []
    for result in detail.all_results or detail.filtered_results:
        box = _rect(getattr(result, "box", None))
        if box is not None:
            boxes.append(box)
    return boxes


@AgentServer.custom_recognition("AllOfIntersect")
class AllOfIntersect(CustomRecognition):
    """组合识别：多个子识别「同时命中」的重叠部分，再按 order_by / index 取一个。

    语义相当于一个「能列出全部交集候选」的 And：
      - **第一个子识别**的结果框作为候选（比如 TemplateMatch 的每个按钮框）；
      - 候选框若与其余每个子识别都有结果框重叠（交集面积占候选框面积
        ≥ min_overlap），才算「同时命中」；
      - 通过的候选按 order_by 排序，index 选第几个，返回它的框（box_from 决定返回哪个子识别的框）。

    典型用途：模板（按钮外框）∩ 颜色连通块（按钮已点亮/可点击），把「已置灰」的按钮排除掉。

    `custom_recognition_param`（JSON 字符串）::

        {
            "all_of": [
                {"type": "TemplateMatch", "param": {"template": "a.png", "roi": [0, 0, 100, 100]}},
                "SomeExistingNode"
            ],
            "order_by": "Vertical",
            "index": 0
        }

    - `all_of`：必选，至少 2 个。元素为节点名（跑该节点的识别）或内联识别定义
    - `order_by`：`Vertical`（默认，最靠上优先，同一行从左到右）/
      `Horizontal` / `Area` / `Random`
    - `index`：取第几个，默认 0；支持负数（-1 为最后一个）
    - `box_from`：返回第几个子识别的框，默认 0（通常是模板框）
    - `min_overlap`：交集面积占候选框面积的最小比例，默认 0（有任何重叠即可）
    """

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        try:
            params = parse_params(argv.custom_recognition_param)
        except ValueError as error:
            logger.error("AllOfIntersect: {}", error)
            return None

        try:
            return self._analyze(context, argv, params)
        except Exception:
            # ctypes 回调里未捕获的异常会被 MaaFW 吞掉，这里显式返回 None（识别失败）
            logger.exception("AllOfIntersect: analyze 异常，按识别失败处理")
            return None

    def _analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
        params: dict[str, Any],
    ) -> CustomRecognition.AnalyzeResult | None:
        subs = params.get("all_of")
        if not isinstance(subs, list) or len(subs) < 2:
            logger.error("AllOfIntersect: all_of 必须是至少含 2 个子识别的列表")
            return None

        min_overlap = float(params.get("min_overlap", 0.0))
        box_from = int(params.get("box_from", 0))
        order_by = str(params.get("order_by", "Vertical"))
        index = int(params.get("index", 0))

        # 逐个交给 MaaFW 识别，收集每个子识别的全部命中框
        results = [_boxes(_run_sub(context, argv.image, sub)) for sub in subs]

        base = results[0]
        if not base:
            logger.debug("AllOfIntersect: 第一个子识别无命中，按未识别处理")
            return None

        # 交集：候选框必须与其余每个子识别都有结果框重叠
        candidates: list[list[list[int]]] = []
        for box in base:
            pair = [box]
            for other in results[1:]:
                partner = _best_overlap(box, other, min_overlap)
                if partner is None:
                    break
                pair.append(partner)
            else:
                candidates.append(pair)

        if not candidates:
            logger.debug("AllOfIntersect: 无候选框与其他子识别同时命中（交集为空）")
            return None
        if not 0 <= box_from < len(subs):
            logger.warning("AllOfIntersect: box_from={} 超出范围，回退到 0", box_from)
            box_from = 0

        candidates = _sort_candidates(candidates, order_by, box_from)
        if index < 0:
            index += len(candidates)
        if not 0 <= index < len(candidates):
            logger.debug("AllOfIntersect: index={} 超出候选数 {}", index, len(candidates))
            return None

        chosen = candidates[index][box_from]
        logger.debug(
            "AllOfIntersect: 候选 {} 个，按 {} 选中第 {} 个 {}",
            len(candidates),
            order_by,
            index,
            chosen,
        )
        return CustomRecognition.AnalyzeResult(
            box=(chosen[0], chosen[1], chosen[2], chosen[3]),
            detail={
                "candidates": candidates,
                "index": index,
                "order_by": order_by,
            },
        )
