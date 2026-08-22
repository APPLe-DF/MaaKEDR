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
    result = event_stage.CheckEventHub().analyze(
        cast(Context, context), cast(CustomRecognition.AnalyzeArg, _argv())
    )
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
    assert context.templates == ["flare_home.png", "home.png"]
    assert context.overridden == ["EventStage.Start"]


def test_event_hub_routes_unknown_page_to_return_to_home() -> None:
    context = _FakeContext([None, None])

    result = _run(context)

    assert result.detail["status"] == "other"
    assert context.templates == ["flare_home.png", "home.png"]
    assert context.overridden == ["EventStage.ReturnToHome"]


def test_event_hub_activity_only_waits_on_unknown_page() -> None:
    context = _FakeContext([None])
    argv = _argv()
    argv.custom_recognition_param = '{"activity_only":"true"}'

    result = event_stage.CheckEventHub().analyze(
        cast(Context, context), cast(CustomRecognition.AnalyzeArg, argv)
    )

    assert result is None
    assert context.templates == ["flare_home.png"]
    assert context.overridden == []


def test_event_hub_activity_only_does_not_route_stale_global_home() -> None:
    context = _FakeContext([None, _FakeDetail((729, 580, 100, 50))])
    argv = _argv()
    argv.custom_recognition_param = '{"activity_only":"true"}'

    result = event_stage.CheckEventHub().analyze(
        cast(Context, context), cast(CustomRecognition.AnalyzeArg, argv)
    )

    assert result is None
    assert context.templates == ["flare_home.png"]
    assert context.overridden == []


def _event_stage_pipeline() -> dict[str, Any]:
    pipeline_path = Path(__file__).parents[1] / "resource" / "base" / "pipeline" / "event_stage.json"
    return cast(dict[str, Any], json.loads(pipeline_path.read_text(encoding="utf-8")))


def test_event_stage_home_recovery_chains_are_separate() -> None:
    pipeline = _event_stage_pipeline()

    assert pipeline["EventStage.Start"]["post_delay"] == 0
    assert pipeline["EventStage.EventHubAfterClick"]["pre_delay"] == 0
    assert pipeline["EventStage.EventHubAfterClick"]["timeout"] == 30000

    assert pipeline["EventStage.ReturnToHome"]["post_delay"] == 0
    assert pipeline["EventStage.ReturnToHome"]["next"] == ["EventStage.CheckHomePageRecovered"]
    assert pipeline["EventStage.CheckHomePageRecovered"]["timeout"] == 30000
    assert pipeline["EventStage.CheckHomePageRecovered"]["next"] == ["EventStage.Start"]
    assert pipeline["EventStage.CheckHomePageRecovered"]["on_error"] == ["EventStage.ReturnToHome"]

    assert pipeline["EventStage.EventHubShop"]["on_error"] == ["EventStage.CheckHomePageShop"]
    assert pipeline["EventStage.CheckHomePageShop"]["next"] == ["EventStage.StartShop"]
    assert pipeline["EventStage.CheckHomePageShop"]["on_error"] == ["EventStage.ReturnToHomeShop"]
    assert pipeline["EventStage.ReturnToHomeShop"]["next"] == ["EventStage.CheckHomePageRecoveredShop"]
    assert pipeline["EventStage.CheckHomePageRecoveredShop"]["next"] == ["EventStage.StartShop"]
    assert pipeline["EventStage.CheckHomePageRecoveredShop"]["on_error"] == ["EventStage.ReturnToHomeShop"]


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
