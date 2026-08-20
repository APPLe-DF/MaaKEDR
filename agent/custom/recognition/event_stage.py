from __future__ import annotations

import re
from typing import Any

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_recognition import CustomRecognition
from maa.define import OCRResult, RectType
from maa.pipeline import JOCR, JRecognitionType, JTemplateMatch
from utils.logger import logger
from utils.maa_types import all_results_as, results_as
from utils.params import coerce_roi, parse_params


def _ocr_results(detail: Any) -> list[OCRResult]:
    """Return OCR results without requiring RecognitionDetail.hit."""
    if detail is None:
        return []
    results: list[OCRResult] = []
    for attr in ("all_results", "filtered_results"):
        raw_results = getattr(detail, attr, None)
        if not raw_results:
            continue
        results.extend(result for result in raw_results if isinstance(result, OCRResult))
    return results


def _normalize_ocr_text(text: Any) -> str:
    """Normalize OCR text enough to recognize the sold-out badge."""
    normalized = re.sub(r"\s+", "", str(text or ""))
    return (
        normalized.replace("已售馨", "已售罄")
        .replace("售馨", "售罄")
        .replace("已售磬", "已售罄")
        .replace("售磬", "售罄")
    )


def _box_tuple(box: Any) -> tuple[float, float, float, float] | None:
    """Convert a Maa box-like value to numeric x/y/w/h, or return None."""
    if box is None:
        return None
    try:
        values = tuple(float(box[index]) for index in range(4))
    except (TypeError, IndexError, ValueError):
        return None
    if values[2] <= 0 or values[3] <= 0:
        return None
    return values


def _box_center_in_roi(box: Any, roi: list[int]) -> bool:
    """Return whether a result box center belongs to the configured item card."""
    values = _box_tuple(box)
    if values is None:
        return False
    x, y, w, h = values
    center_x, center_y = x + w / 2, y + h / 2
    return roi[0] <= center_x < roi[0] + roi[2] and roi[1] <= center_y < roi[1] + roi[3]


def _sold_out_results(detail: Any) -> list[OCRResult]:
    """Return deduplicated OCR hits containing the sold-out label."""
    raw_results = [
        result for result in _ocr_results(detail) if "售罄" in _normalize_ocr_text(result.text)
    ]
    unique: list[OCRResult] = []
    for result in raw_results:
        box = _box_tuple(result.box)
        if box is None:
            unique.append(result)
            continue
        x, y, w, h = box
        center = (x + w / 2, y + h / 2)
        duplicate = False
        for old in unique:
            old_box = _box_tuple(old.box)
            if old_box is None:
                continue
            old_x, old_y, old_w, old_h = old_box
            if (
                abs(center[0] - (old_x + old_w / 2)) < 50
                and abs(center[1] - (old_y + old_h / 2)) < 35
            ):
                duplicate = True
                break
        if not duplicate:
            unique.append(result)
    return unique


def _distinct_sold_out_count(results: list[OCRResult]) -> int:
    """Return the number of distinct sold-out cards."""
    return len(results)


@AgentServer.custom_recognition("CheckAllSoldOut")
class CheckAllSoldOut(CustomRecognition):
    """Detect the shop's all-sold-out layout from multiple OCR hits."""

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        try:
            params = parse_params(argv.custom_recognition_param)
        except ValueError as error:
            logger.error("CheckAllSoldOut: {}", error)
            return None

        roi = coerce_roi(params.get("roi"), [0, 180, 1280, 540], "CheckAllSoldOut")
        try:
            total_items = int(params.get("total_items", 10))
        except (TypeError, ValueError):
            total_items = 10
        if total_items < 1:
            total_items = 10
        detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(expected=["已售罄"], roi=(roi[0], roi[1], roi[2], roi[3])),
            argv.image,
        )
        # Maa 的 JOCR 结果在不同版本可能把命中结果放入 filtered_results 或 all_results；
        # 只保留本次 OCR 文本中确实包含「售罄」的结果，避免重复框/其他 OCR 结果污染计数。
        results = _sold_out_results(detail)
        sold_out_count = _distinct_sold_out_count(results)
        first_box = results[0].box if results and results[0].box else (0, 0, 1, 1)
        if sold_out_count < total_items:
            # 仅命中少数售罄标记时，必须从商品 1 开始逐件检查，不能把“2 个标记”误判为全部售罄。
            context.override_next(argv.node_name, ["EventStage.CheckSoldOut1"])
            logger.info(
                "[活动商店] 未全部售罄（命中 {}/{} 个标记），从商品1开始逐件检查购买",
                sold_out_count,
                total_items,
            )
            return CustomRecognition.AnalyzeResult(
                box=first_box, detail={"status": "not_all_sold_out", "count": sold_out_count}
            )

        # 只有达到商品总数才进入全部售罄分支；否则 SelectFixedGuarantee 会按 override 路由。
        context.override_next(argv.node_name, ["EventStage.ShopAllSoldOut"])
        logger.info(
            "[活动商店] 检测到全部商品售罄（{}/{} 个标记）", sold_out_count, total_items
        )
        return CustomRecognition.AnalyzeResult(
            box=first_box, detail={"status": "all_sold_out", "count": sold_out_count}
        )


@AgentServer.custom_recognition("CheckShopItemSoldOut")
class CheckShopItemSoldOut(CustomRecognition):
    """Route each shop item without relying on pipeline on_error handling."""

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        try:
            params = parse_params(argv.custom_recognition_param)
            item_roi = coerce_roi(params.get("roi"), [0, 180, 1280, 540], "CheckShopItemSoldOut")
            shop_roi = coerce_roi(params.get("shop_roi"), [0, 180, 1280, 540], "CheckShopItemSoldOut")
            sold_out_next = str(params["sold_out_next"])
            buy_next = str(params["buy_next"])
            detail = context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(expected=[], roi=(shop_roi[0], shop_roi[1], shop_roi[2], shop_roi[3])),
                argv.image,
            )
            all_results = _sold_out_results(detail)
            matching_results = [
                result for result in all_results if _box_center_in_roi(result.box, item_roi)
            ]
            if matching_results:
                target, status = sold_out_next, "sold_out"
            else:
                target, status = buy_next, "available"
            context.override_next(argv.node_name, [target])
            logger.info(
                "[活动商店] 商品{}: {} -> {}（OCR售罄框: {}）",
                params.get("item", "?"),
                status,
                target,
                [result.box for result in matching_results],
            )
            box = matching_results[0].box if matching_results and matching_results[0].box else (0, 0, 1, 1)
            return CustomRecognition.AnalyzeResult(box=box, detail={"status": status})
        except (KeyError, TypeError, ValueError) as error:
            logger.error("CheckShopItemSoldOut: {}", error)
            return None


@AgentServer.custom_recognition("CheckShopRefreshAfterPurchase")
class CheckShopRefreshAfterPurchase(CustomRecognition):
    """确认购买完成后商店状态已刷新，否则触发一次安全补点。"""

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        try:
            params = parse_params(argv.custom_recognition_param)
            shop_roi = coerce_roi(
                params.get("shop_roi"), [0, 180, 1280, 540], "CheckShopRefreshAfterPurchase"
            )
            ready_next = str(params["ready_next"])
            refresh_next = str(params["refresh_next"])
            detail = context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(expected=[], roi=(shop_roi[0], shop_roi[1], shop_roi[2], shop_roi[3])),
                argv.image,
            )
            sold_out_results = _sold_out_results(detail)
            if sold_out_results:
                target, status = ready_next, "refreshed"
                box = sold_out_results[0].box or (0, 0, 1, 1)
                logger.info("[活动商店] 完成购买返回商店：状态已刷新，继续检查")
            else:
                target, status = refresh_next, "refresh_needed"
                box = (0, 0, 1, 1)
                logger.info("[活动商店] 完成购买返回商店：状态未更新，左侧补点一次")
            context.override_next(argv.node_name, [target])
            return CustomRecognition.AnalyzeResult(
                box=box, detail={"status": status, "sold_out_count": len(sold_out_results)}
            )
        except (KeyError, TypeError, ValueError) as error:
            logger.error("CheckShopRefreshAfterPurchase: {}", error)
            return None


@AgentServer.custom_recognition("CheckStageExhausted")
class CheckStageExhausted(CustomRecognition):
    """Detect the stage card counter only when it is exactly 0/3."""

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        try:
            params = parse_params(argv.custom_recognition_param)
        except ValueError as error:
            logger.error("CheckStageExhausted: {}", error)
            return None

        roi = coerce_roi(params.get("stage_roi"), [280, 90, 720, 100], "CheckStageExhausted")
        detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(expected=[r"^0/3$"], roi=(roi[0], roi[1], roi[2], roi[3]), only_rec=True),
            argv.image,
        )
        results = results_as(detail, OCRResult)
        if len(results) != 1:
            return None

        result = results[0]
        if not result.box or not result.text:
            return None
        text = re.sub(r"\s+", "", result.text.strip()).replace("／", "/").replace("O", "0")
        if re.fullmatch(r"0/3", text) is None:
            return None

        logger.info("[活动刷取] 关卡次数已耗尽: {}", text)
        return CustomRecognition.AnalyzeResult(
            box=result.box,
            detail={"status": "exhausted", "count": 0, "total": 3, "text": text},
        )



@AgentServer.custom_recognition("CheckEventStage")
class CheckEventStage(CustomRecognition):
    """检测活动关卡（按参数传入关卡名与识别区域，OCR 定位）"""

    def _stage_roi_or_none(self, stage_roi: list[int]) -> tuple[int, int, int, int] | None:
        result = coerce_roi(stage_roi, [-1, -1, -1, -1], "CheckEventStage")
        if result == [-1, -1, -1, -1]:
            return None
        return result[0], result[1], result[2], result[3]

    def _count_roi_or_none(
        self, raw: Any, box: RectType | None
    ) -> tuple[int, int, int, int] | None:
        """优先使用显式 count_roi（task 选项可能覆盖）；否则按关卡卡片位置推导。

        次数徽标（如 0/3）位于卡片左上角上方约 36~40px，宽度约为卡片宽 -17px
        （EX2-1 卡片 [947,510,89,38] → 徽标 [957,474,72,29]；
         EX4-1 卡片 [942,217,89,39] → 徽标 [955,178,71,38]，两例一致）。
        raw 为 None/非法时不告警，直接静默回退为基于 box 的推导，避免默认 ROI
        [280,90,720,100] 扫描噪声与「ROI 配置无效」日志刷屏。
        """
        if raw is not None:
            explicit = coerce_roi(raw, [-1, -1, -1, -1], "CheckEventStage")
            if explicit != [-1, -1, -1, -1]:
                return explicit[0], explicit[1], explicit[2], explicit[3]
        if box is None:
            return None
        # box 可能是 maa.define.Rect（无 __len__，但支持下标/迭代）或 list/tuple
        try:
            x, y, w, _h = (int(box[0]), int(box[1]), int(box[2]), int(box[3]))
        except (TypeError, IndexError, ValueError):
            return None
        return max(x - 10, 0), max(y - 50, 0), max(w + 20, 100), 55

    def _check_locked(
        self,
        context: Context,
        image: Any,
        stage_roi: list[int],
        lock_template: str,
        lock_threshold: float,
    ) -> tuple[int, int, int, int] | None:
        if not lock_template:
            return None
        roi_tuple = self._stage_roi_or_none(stage_roi)
        if roi_tuple is None:
            return None
        try:
            lock_detail = context.run_recognition_direct(
                JRecognitionType.TemplateMatch,
                JTemplateMatch(
                    template=[lock_template],
                    roi=roi_tuple,
                    threshold=[lock_threshold],
                ),
                image,
            )
            if lock_detail and lock_detail.box:
                box = lock_detail.box
                return (int(box[0]), int(box[1]), int(box[2]), int(box[3]))
        except Exception:
            return None
        return None

    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult | RectType | None:
        try:
            params = parse_params(argv.custom_recognition_param)
        except ValueError as error:
            logger.error("CheckEventStage: {}", error)
            return None

        stage_name = params.get("stage_name", "")
        stage_roi = coerce_roi(params.get("stage_roi"), [0, 0, 1280, 640], "CheckEventStage")
        lock_template = params.get("lock_template", "")
        lock_threshold = params.get("lock_threshold", 0.7)

        if not stage_name:
            logger.error("CheckEventStage: stage_name 为空")
            return None

        roi_tuple = self._stage_roi_or_none(stage_roi)
        if roi_tuple is None:
            return None

        image = argv.image

        lock_box = None
        if lock_template:
            lock_box = self._check_locked(context, image, stage_roi, lock_template, lock_threshold)
        if lock_box is not None:
            logger.warning("[活动刷取] {} 关卡被锁定", stage_name)
            context.override_next(argv.node_name, ["EventStage.StageLocked"])
            return CustomRecognition.AnalyzeResult(box=lock_box, detail={"status": "locked"})

        stage_name_no_dash = stage_name.replace("-", "")
        ocr_detail = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(
                expected=[stage_name, stage_name_no_dash],
                roi=roi_tuple,
            ),
            image,
        )

        if not ocr_detail or not ocr_detail.box:
            # 目标关卡不在当前视野：路由到向右滑动，滑完回来再找（EX4-1 在最右需滑到底）
            context.override_next(argv.node_name, ["EventStage.DragFindStage"])
            logger.info("[活动刷取] 未找到关卡 {}，向右滑动地图", stage_name)
            return CustomRecognition.AnalyzeResult(box=(400, 300, 1, 1), detail={"status": "not_found"})

        # 已找到关卡：在其上方徽标区域检查次数是否耗尽（0/3）。
        # 原实现先在全屏默认 ROI 上扫 0/3：EX 关图标实际在 y>170 处（EX4-1 徽标 [955,178]），
        # 默认 ROI [280,90,720,100] 覆盖不全导致误判漏判，且每次识别都告警刷屏；
        # 且 run-2 中已耗尽的 EX2-1 被点击后不进入 event5，CheckQuickBattleState 只能空转超时。
        player_box = ocr_detail.box
        count_roi = self._count_roi_or_none(params.get("count_roi"), player_box)
        if count_roi is not None:
            # 不使用 expected/only_rec 过滤：游戏中的徽标 OCR 可能带空格、全角符号或 O/0 混淆，
            # 先拿到 ROI 内全部文本，再归一化判断，避免耗尽关卡被误点击后在 StagePrepare 空转。
            count_detail = context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(expected=[], roi=count_roi),
                image,
            )
            count_results = all_results_as(count_detail, OCRResult)
            for count_result in count_results:
                raw_count_text = count_result.text or ""
                count_text = (
                    re.sub(r"\s+", "", raw_count_text)
                    .replace("／", "/")
                    .replace("O", "0")
                    .replace("o", "0")
                )
                if re.search(r"0/3", count_text):
                    logger.info("[活动刷取] {} 关卡次数已耗尽，徽标文本: {}", stage_name, raw_count_text)
                    context.override_next(argv.node_name, ["EventStage.ReturnMainFromStage"])
                    return CustomRecognition.AnalyzeResult(
                        box=count_result.box or player_box,
                        detail={"status": "exhausted", "text": count_text},
                    )

        # 找到目标：显式恢复路由到战斗准备，避免之前滑动分支的 override 残留
        context.override_next(argv.node_name, ["EventStage.StagePrepare"])

        logger.info("[活动刷取] 找到关卡 {}，位置: {}", stage_name, player_box)
        return CustomRecognition.AnalyzeResult(box=player_box, detail={"status": "found"})
