from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from custom.recognition import event_stage
from maa.context import Context
from maa.custom_recognition import CustomRecognition


class _FakeDetail:
    def __init__(self, box: tuple[int, int, int, int] | None = None) -> None:
        self.box = box


class _FakeContext:
    def __init__(self, details: list[_FakeDetail | None]) -> None:
        self._details = iter(details)
        self.templates: list[str] = []
        self.overridden: list[str] = []

    def run_recognition_direct(self, _recognition_type: Any, recognition: Any, _image: Any) -> _FakeDetail | None:
        self.templates.append(recognition.template[0])
        return next(self._details)

    def override_next(self, _node_name: str, next_nodes: list[str]) -> None:
        self.overridden = next_nodes


def _argv() -> SimpleNamespace:
    return SimpleNamespace(custom_recognition_param="", image=object(), node_name="EventStage.EventHub")


def _run(context: _FakeContext) -> CustomRecognition.AnalyzeResult:
    result = event_stage.CheckEventHub().analyze(cast(Context, context), cast(CustomRecognition.AnalyzeArg, _argv()))
    assert result is not None
    return cast(CustomRecognition.AnalyzeResult, result)


def test_event_hub_routes_activity_home_to_journey() -> None:
    context = _FakeContext([_FakeDetail((100, 100, 10, 10))])

    result = _run(context)

    assert result.detail["status"] == "activity_home"
    assert context.templates == ["flare_home.png"]
    assert context.overridden == ["EventStage.ClickJourney"]


def test_event_hub_routes_global_home_to_start() -> None:
    context = _FakeContext([None, _FakeDetail((100, 100, 10, 10))])

    result = _run(context)

    assert result.detail["status"] == "global_home"
    assert context.templates == ["flare_home.png", "main_option.png"]
    assert context.overridden == ["EventStage.Start"]


def test_event_hub_routes_unknown_page_to_ensure_home() -> None:
    context = _FakeContext([None, None])

    result = _run(context)

    assert result.detail["status"] == "other"
    assert context.templates == ["flare_home.png", "main_option.png"]
    assert context.overridden == ["EventStage.EnsureHome"]


def test_event_hub_activity_only_waits_on_unknown_page() -> None:
    context = _FakeContext([None])
    argv = _argv()
    argv.custom_recognition_param = '{"activity_only":"true"}'

    result = event_stage.CheckEventHub().analyze(cast(Context, context), cast(CustomRecognition.AnalyzeArg, argv))

    assert result is None
    assert context.templates == ["flare_home.png"]
    assert context.overridden == []


def test_event_hub_activity_only_does_not_route_stale_global_home() -> None:
    context = _FakeContext([None, _FakeDetail((729, 580, 100, 50))])
    argv = _argv()
    argv.custom_recognition_param = '{"activity_only":"true"}'

    result = event_stage.CheckEventHub().analyze(cast(Context, context), cast(CustomRecognition.AnalyzeArg, argv))

    assert result is None
    assert context.templates == ["flare_home.png"]
    assert context.overridden == []


def _event_stage_pipeline() -> dict[str, Any]:
    pipeline_path = Path(__file__).parents[1] / "resource" / "base" / "pipeline" / "event_stage.json"
    return cast(dict[str, Any], json.loads(pipeline_path.read_text(encoding="utf-8")))


# #54 删掉各自为政的回主页链后新增的意外引用点，都会在运行期才炸。
_RETIRED_NODES = frozenset(
    {
        "EventStage.ReturnToHome",
        "EventStage.ReturnToHomeShop",
        "EventStage.CheckHomePageRecovered",
        "EventStage.CheckHomePageRecoveredShop",
    }
)


def _merged_pipeline() -> dict[str, Any]:
    """按 interface.json 的 resource 顺序合并全部 Bundle 的 pipeline。

    节点表是跨文件合并的单一命名空间，只扫单个文件看不见跨 Bundle 的悬空引用。
    """
    root = Path(__file__).parents[1]
    interface = cast(dict[str, Any], json.loads((root / "interface.json").read_text(encoding="utf-8")))
    merged: dict[str, Any] = {}
    for resource in interface["resource"]:
        for bundle in resource["path"]:
            pipeline_dir = root / bundle.lstrip("./") / "pipeline"
            if not pipeline_dir.is_dir():
                continue
            for file_path in sorted(pipeline_dir.glob("*.json")):
                merged.update(cast(dict[str, Any], json.loads(file_path.read_text(encoding="utf-8"))))
    return merged


def test_event_stage_home_recovery_goes_through_common_hub() -> None:
    pipeline = _event_stage_pipeline()

    assert pipeline["EventStage.Start"]["post_delay"] == 0
    assert pipeline["EventStage.EventHubAfterClick"]["pre_delay"] == 0
    assert pipeline["EventStage.EventHubAfterClick"]["timeout"] == 30000

    # 回主页统一由 Common.EnsureHome 枢纽承担，本任务只保留「已在主页则继续」的确认门。
    assert pipeline["EventStage.EnsureHome"]["next"] == [
        "EventStage.CheckHomePage",
        "[JumpBack]Common.EnsureHome",
    ]
    assert pipeline["EventStage.CheckHomePage"]["next"] == [
        "EventStage.Start",
        "[JumpBack]Common.EnsureHome",
    ]
    assert pipeline["EventStage.CheckHomePage"]["template"] == "main_option.png"

    assert pipeline["EventStage.EventHubShop"]["on_error"] == ["EventStage.EnsureHomeShop"]
    assert pipeline["EventStage.EnsureHomeShop"]["next"] == [
        "EventStage.CheckHomePageShop",
        "[JumpBack]Common.EnsureHome",
    ]
    assert pipeline["EventStage.CheckHomePageShop"]["next"] == [
        "EventStage.StartShop",
        "[JumpBack]Common.EnsureHome",
    ]


def test_event_stage_has_no_retired_home_recovery_nodes() -> None:
    merged = _merged_pipeline()

    # 各自为政的旧回主页链已删除（#54）。残留引用会在运行期才炸，这里跨全部资源包静态挡住——
    # CheckEventHub 的 other_next 默认值与 pipeline 里各节点的显式传参都可能是漏网的引用点。
    for retired in (
        "EventStage.ReturnToHome",
        "EventStage.ReturnToHomeShop",
        "EventStage.CheckHomePageRecovered",
        "EventStage.CheckHomePageRecoveredShop",
    ):
        assert retired not in merged

    # 合并后的节点表里不得有任何 next / on_error 指向已退役节点。
    dangling = [
        f"{node} -> {ref}"
        for node, definition in merged.items()
        if isinstance(definition, dict)
        for ref in [
            *definition.get("next", []),
            *definition.get("on_error", []),
        ]
        if isinstance(ref, str) and ref.removeprefix("[JumpBack]") in _RETIRED_NODES
    ]
    assert dangling == []


def test_event_stage_battle_handles_item_dialog_before_returning_home() -> None:
    pipeline = _event_stage_pipeline()
    battle_stage = pipeline["EventStage.BattleStage"]
    item_dialog = pipeline["EventStage.ClickItemDialog"]
    check_back = pipeline["EventStage.CheckBackOnMap"]

    assert battle_stage["next"][:2] == [
        "[JumpBack]EventStage.ClickVictory",
        "[JumpBack]EventStage.ClickItemDialog",
    ]
    assert item_dialog["template"] == "item_obtained_dialog.png"
    assert item_dialog["roi"] == [500, 150, 280, 180]
    assert item_dialog["repeat"] == 2
    assert item_dialog["repeat_delay"] == 500
    assert item_dialog["post_delay"] == 1000
    assert check_back["next"] == ["EventStage.ReturnMainFromStage"]


def test_event_stage_return_home_waits_for_slow_transition() -> None:
    pipeline = _event_stage_pipeline()

    # 点击活动地图 HOME 后游戏转场回全局主页约需 6s；
    # 验证窗口必须足够长，否则 CheckReturnedHome 尚未命中就超时导致任务误报失败。
    assert pipeline["EventStage.ReturnMainFromStage"]["timeout"] >= 10000
    assert pipeline["EventStage.ReturnMainFromStage"]["next"] == ["EventStage.CheckReturnedHome"]
    assert pipeline["EventStage.CheckReturnedHome"]["template"] == "main_option.png"
