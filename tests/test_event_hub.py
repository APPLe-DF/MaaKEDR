from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest
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


@pytest.fixture(autouse=True)
def _use_fake_detail(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    monkeypatch.setattr(event_stage, "OCRResult", _FakeDetail)


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
