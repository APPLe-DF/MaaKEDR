from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from custom.recognition import general
from maa.context import Context
from maa.custom_recognition import CustomRecognition

PIPELINE_PATH = Path(__file__).parents[1] / "resource" / "base" / "pipeline" / "send_gift.json"
TASK_PATH = Path(__file__).parents[1] / "tasks" / "send_gift.json"


class _Result:
    def __init__(self, box: list[int]) -> None:
        self.box = box


class _Detail:
    def __init__(self, boxes: list[list[int]]) -> None:
        self.hit = bool(boxes)
        self.box = boxes[0] if boxes else None
        self.all_results = [_Result(box) for box in boxes]
        self.filtered_results = self.all_results
        self.best_result = self.all_results[0] if self.all_results else None


class _FakeContext:
    """按内联类型返回预置结果，并记录调用参数。"""

    def __init__(self, template_boxes: list[list[int]], color_boxes: list[list[int]]) -> None:
        self.template_boxes = template_boxes
        self.color_boxes = color_boxes
        self.direct_calls: list[tuple[str, Any]] = []
        self.node_calls: list[str] = []

    def run_recognition_direct(self, reco_type: Any, param: Any, _image: Any) -> _Detail:
        self.direct_calls.append((str(reco_type), param))
        boxes = self.template_boxes if "TemplateMatch" in str(reco_type) else self.color_boxes
        return _Detail(boxes)

    def run_recognition(self, node_name: str, _image: Any) -> _Detail:
        self.node_calls.append(node_name)
        return _Detail(self.template_boxes)


def _argv(param: dict[str, Any] | str) -> SimpleNamespace:
    raw = param if isinstance(param, str) else json.dumps(param)
    return SimpleNamespace(custom_recognition_param=raw, image=object(), node_name="SendGift.Do")


def _analyze(context: _FakeContext, param: dict[str, Any] | str) -> CustomRecognition.AnalyzeResult | None:
    result = general.AllOfIntersect().analyze(
        cast(Context, context),
        cast(CustomRecognition.AnalyzeArg, _argv(param)),
    )
    assert result is None or isinstance(result, CustomRecognition.AnalyzeResult)
    return result


SEND_GIFT_PARAM: dict[str, Any] = {
    "all_of": [
        {
            "type": "TemplateMatch",
            "param": {"template": "send_gift/gift_button.png", "roi": [970, 110, 125, 595], "green_mask": True},
        },
        {
            "type": "ColorMatch",
            "param": {
                "roi": [970, 110, 125, 595],
                "lower": [235, 235, 80],
                "upper": [255, 255, 115],
                "connected": True,
                "count": 600,
            },
        },
    ],
    "order_by": "Vertical",
    "index": 0,
}


class TestAllOfIntersectSendGift:
    def test_skips_gifted_button_without_gold_block(self) -> None:
        """三个赠送图标里只有最下面那块是金色的：交集后只剩它，且被选中。"""
        context = _FakeContext(
            template_boxes=[[982, 169, 100, 100], [982, 269, 100, 100], [982, 369, 100, 100]],
            color_boxes=[[990, 380, 80, 40]],
        )

        result = _analyze(context, SEND_GIFT_PARAM)

        assert result is not None
        assert result.box == (982, 369, 100, 100)

    def test_vertical_order_picks_topmost(self) -> None:
        context = _FakeContext(
            template_boxes=[[982, 369, 100, 100], [982, 169, 100, 100]],
            color_boxes=[[990, 180, 80, 40], [990, 380, 80, 40]],
        )

        result = _analyze(context, SEND_GIFT_PARAM)

        assert result is not None
        assert result.box == (982, 169, 100, 100)

    def test_index_one_picks_second_candidate(self) -> None:
        params = dict(SEND_GIFT_PARAM, index=1)
        context = _FakeContext(
            template_boxes=[[982, 169, 100, 100], [982, 369, 100, 100]],
            color_boxes=[[990, 180, 80, 40], [990, 380, 80, 40]],
        )

        result = _analyze(context, params)

        assert result is not None
        assert result.box == (982, 369, 100, 100)

    def test_no_overlap_returns_none(self) -> None:
        context = _FakeContext(
            template_boxes=[[982, 169, 100, 100]],
            color_boxes=[[100, 600, 20, 20]],
        )

        assert _analyze(context, SEND_GIFT_PARAM) is None

    def test_empty_template_hit_returns_none(self) -> None:
        context = _FakeContext(template_boxes=[], color_boxes=[[990, 180, 80, 40]])

        assert _analyze(context, SEND_GIFT_PARAM) is None

    def test_index_out_of_range_returns_none(self) -> None:
        params = dict(SEND_GIFT_PARAM, index=5)
        context = _FakeContext(
            template_boxes=[[982, 169, 100, 100]],
            color_boxes=[[990, 180, 80, 40]],
        )

        assert _analyze(context, params) is None

    def test_scalar_template_is_normalized_to_list(self) -> None:
        context = _FakeContext(
            template_boxes=[[982, 169, 100, 100]],
            color_boxes=[[990, 180, 80, 40]],
        )

        _analyze(context, SEND_GIFT_PARAM)

        reco_type, param = context.direct_calls[0]
        assert "TemplateMatch" in reco_type
        assert param.template == ["send_gift/gift_button.png"]
        assert "ColorMatch" in context.direct_calls[1][0]

    def test_node_name_sub_runs_node_recognition(self) -> None:
        params = {
            "all_of": ["SomeExistingNode", SEND_GIFT_PARAM["all_of"][1]],
            "order_by": "Vertical",
        }
        context = _FakeContext(
            template_boxes=[[982, 169, 100, 100]],
            color_boxes=[[990, 180, 80, 40]],
        )

        result = _analyze(context, params)

        assert result is not None
        assert context.node_calls == ["SomeExistingNode"]

    def test_fewer_than_two_subs_returns_none(self) -> None:
        context = _FakeContext(template_boxes=[[982, 169, 100, 100]], color_boxes=[])

        assert _analyze(context, {"all_of": ["SomeExistingNode"]}) is None


class TestGeometryHelpers:
    def test_intersection_area_of_half_overlap(self) -> None:
        assert general._intersection_area([0, 0, 10, 10], [5, 0, 10, 10]) == 50

    def test_intersection_area_when_disjoint(self) -> None:
        assert general._intersection_area([0, 0, 10, 10], [20, 20, 10, 10]) == 0

    def test_rect_accepts_mapping_and_rejects_empty(self) -> None:
        assert general._rect({"x": 1, "y": 2, "w": 3, "h": 4}) == [1, 2, 3, 4]
        assert general._rect([1, 2, 3, 4]) == [1, 2, 3, 4]
        assert general._rect([1, 2, 0, 4]) is None
        assert general._rect(None) is None

    def test_sort_random_keeps_all_candidates(self) -> None:
        candidates = [[[0, 10, 10, 10]], [[0, 5, 10, 10]]]

        shuffled = general._sort_candidates(candidates, "Random", 0)

        assert sorted(shuffled) == sorted(candidates)


class TestSendGiftPipeline:
    def _pipeline(self) -> dict[str, Any]:
        return cast(dict[str, Any], json.loads(PIPELINE_PATH.read_text(encoding="utf-8")))

    def test_task_entry_points_at_gate_node(self) -> None:
        tasks = cast(dict[str, Any], json.loads(TASK_PATH.read_text(encoding="utf-8")))
        pipeline = self._pipeline()

        task = tasks["task"][0]
        assert task["entry"] == "SendGift.EnsureHome"
        assert task["group"] == ["Daily"]
        assert task["entry"] in pipeline

    def test_loop_matches_mak_node_chain(self) -> None:
        pipeline = self._pipeline()

        assert pipeline["SendGift.Loop"]["next"] == [
            "SendGift.QuotaFull",
            "[JumpBack]SendGift.Step",
            "SendGift.Finish",
        ]
        assert pipeline["SendGift.Step"]["next"] == ["SendGift.Do", "SendGift.Swipe"]
        assert pipeline["SendGift.Do"]["next"] == ["SendGift.Swipe"]
        assert "next" not in pipeline["SendGift.Swipe"]
        assert pipeline["SendGift.Step"]["max_hit"] == 50
        assert pipeline["SendGift.Do"]["max_hit"] == 20

    def test_quota_full_reads_daily_limit(self) -> None:
        node = self._pipeline()["SendGift.QuotaFull"]

        assert node["recognition"] == "OCR"
        assert node["roi"] == [1120, 665, 135, 25]
        assert node["expected"] == "20\\s*[/／]\\s*20"
        assert node["next"] == ["SendGift.Finish"]

    def test_do_node_param_decodes_to_mak_intersection(self) -> None:
        node = self._pipeline()["SendGift.Do"]

        assert node["custom_recognition"] == "AllOfIntersect"
        assert node["action"] == {"type": "Click"}
        # 与 MAK 一样直接写 JSON 对象：写成 JSON 字符串会被 MaaFW 再序列化一次（双重转义）
        params = node["custom_recognition_param"]
        assert isinstance(params, dict)
        assert params["order_by"] == "Vertical"
        assert params["index"] == 0
        template, color = params["all_of"]
        assert template["type"] == "TemplateMatch"
        assert template["param"]["template"] == "send_gift/gift_button.png"
        assert template["param"]["roi"] == [970, 110, 125, 595]
        assert template["param"]["green_mask"] is True
        assert color["type"] == "ColorMatch"
        assert color["param"]["lower"] == [235, 235, 80]
        assert color["param"]["upper"] == [255, 255, 115]
        assert color["param"]["connected"] is True
        assert color["param"]["count"] == 600

    def test_swipe_matches_mak_gesture(self) -> None:
        node = self._pipeline()["SendGift.Swipe"]

        assert node["action"]["type"] == "Swipe"
        assert node["action"]["param"]["begin"] == [680, 420, 200, 10]
        assert node["action"]["param"]["end"] == [680, 270, 200, 10]
        assert node["action"]["param"]["end_hold"] == 1000

    def test_navigation_uses_home_hub(self) -> None:
        pipeline = self._pipeline()

        assert "[JumpBack]Common.EnsureHome" in pipeline["SendGift.EnsureHome"]["next"]
        assert pipeline["SendGift.EnsureHome"]["next"][0] == "SendGift.CheckHomePage"
        assert pipeline["SendGift.CheckFriendList"]["next"] == ["SendGift.Loop"]
        assert pipeline["SendGift.ClickFriendEntry"]["next"][0] == "SendGift.CheckFriendList"
