from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from custom.recognition import stamina
from maa.context import Context
from maa.custom_recognition import CustomRecognition


class _FakeDetail:
    def __init__(self, box: tuple[int, int, int, int] | None = None) -> None:
        self.box = box


class _FakeContext:
    def __init__(self, detail: _FakeDetail | None) -> None:
        self._detail = detail
        self.templates: list[str] = []
        self.rois: list[tuple[int, int, int, int]] = []
        self.overridden: list[str] = []
        self.override_ok = True

    def run_recognition_direct(self, _recognition_type: Any, recognition: Any, _image: Any) -> _FakeDetail | None:
        self.templates.append(recognition.template[0])
        self.rois.append(recognition.roi)
        return self._detail

    def override_next(self, _node_name: str, next_nodes: list[str]) -> bool:
        self.overridden = next_nodes
        return self.override_ok


def _argv(param: str = "") -> SimpleNamespace:
    return SimpleNamespace(custom_recognition_param=param, image=object(), node_name="StaminaInfo")


def _run(context: _FakeContext, param: str = "") -> CustomRecognition.AnalyzeResult | None:
    return stamina.CheckStaminaPage().analyze(cast(Context, context), cast(CustomRecognition.AnalyzeArg, _argv(param)))


def test_stamina_page_routes_home_to_read() -> None:
    context = _FakeContext(_FakeDetail((1199, 6, 77, 83)))

    result = _run(context)

    assert result is not None
    assert result.detail["status"] == "home"
    assert context.templates == ["main_option.png"]
    assert context.rois == [(1199, 6, 77, 83)]
    assert context.overridden == ["StaminaInfo.Read", "StaminaInfo.ReadRetry"]


def test_stamina_page_accepts_single_string_home_next() -> None:
    context = _FakeContext(_FakeDetail((1199, 6, 77, 83)))
    param = '{"home_next": "StaminaInfo.Read"}'

    result = _run(context, param)

    assert result is not None
    assert context.overridden == ["StaminaInfo.Read"]


def test_stamina_page_routes_other_page_to_click_home() -> None:
    context = _FakeContext(None)

    result = _run(context)

    assert result is not None
    assert result.detail["status"] == "other"
    assert context.overridden == ["StaminaInfo.ClickHome", "StaminaInfo.ClickHomeRetry"]


def test_stamina_page_gives_up_after_other_max() -> None:
    context = _FakeContext(None)
    recognition = stamina.CheckStaminaPage()

    results = [
        recognition.analyze(cast(Context, context), cast(CustomRecognition.AnalyzeArg, _argv())) for _ in range(4)
    ]

    # 前 3 次路由到 ClickHome（点击返回主页），第 4 次放弃（None → 任务失败）
    assert [result.detail["status"] if result else None for result in results] == [
        "other",
        "other",
        "other",
        None,
    ]
    assert context.overridden == ["StaminaInfo.ClickHome", "StaminaInfo.ClickHomeRetry"]


def test_stamina_page_resets_counter_when_home_reached() -> None:
    recognition = stamina.CheckStaminaPage()
    argv = cast(CustomRecognition.AnalyzeArg, _argv())

    other_context = _FakeContext(None)
    assert recognition.analyze(cast(Context, other_context), argv) is not None
    assert recognition.analyze(cast(Context, other_context), argv) is not None

    home_context = _FakeContext(_FakeDetail((1199, 6, 77, 83)))
    assert recognition.analyze(cast(Context, home_context), argv) is not None
    assert home_context.overridden == ["StaminaInfo.Read", "StaminaInfo.ReadRetry"]

    # 回到主界面后计数复位，再次不在主界面仍可继续尝试 ClickHome
    other_context = _FakeContext(None)
    result = recognition.analyze(cast(Context, other_context), argv)
    assert result is not None
    assert other_context.overridden == ["StaminaInfo.ClickHome", "StaminaInfo.ClickHomeRetry"]


def test_stamina_page_override_next_failure_returns_none() -> None:
    context = _FakeContext(_FakeDetail((1199, 6, 77, 83)))
    context.override_ok = False

    result = _run(context)

    assert result is None


def _stamina_pipeline() -> dict[str, Any]:
    pipeline_path = Path(__file__).parents[1] / "resource" / "base" / "pipeline" / "stamina.json"
    return cast(dict[str, Any], json.loads(pipeline_path.read_text(encoding="utf-8")))


def test_stamina_pipeline_read_failure_cannot_reach_click_home() -> None:
    """回归：读取失败时不得通过 next 回落到 ClickHome（循环根因）。

    旧实现把 Read 与 ClickHome 并列在入口节点的 next 中，Read 识别失败会顺序
    回落到 ClickHome，而 ClickHome 在主界面同样命中并点击，形成无限循环。
    """
    pipeline = _stamina_pipeline()

    assert pipeline["StaminaInfo"]["recognition"] == "Custom"
    assert pipeline["StaminaInfo"]["custom_recognition"] == "CheckStaminaPage"
    assert pipeline["StaminaInfo"]["next"] == ["StaminaInfo.Read", "StaminaInfo.ReadRetry"]
    assert "StaminaInfo.ClickHome" not in pipeline["StaminaInfo"]["next"]

    assert "next" not in pipeline["StaminaInfo.Read"]
    assert pipeline["StaminaInfo.ClickHome"]["next"] == ["StaminaInfo"]


def test_stamina_pipeline_read_retried_at_most_twice() -> None:
    """回归：读取识别最多尝试 3 次（首次 + ReadRetry 重试 2 次），而不是超时 60 秒。

    - ReadRetry 为 DirectHit 闸门：每次命中 = 一次重试，max_hit=2 → 合计 3 次读取；
    - timeout=0：每轮截图只识别一次，尝试次数与设备速度无关；
    - 耗尽后闸门被跳过 → 列表失败 → 任务失败（读取失败 → 任务失败）。
    """
    pipeline = _stamina_pipeline()

    read_retry = pipeline["StaminaInfo.ReadRetry"]
    assert read_retry["recognition"] == "DirectHit"
    assert read_retry["max_hit"] == 2
    assert read_retry["timeout"] == 0
    assert read_retry["next"] == ["StaminaInfo.Read", "StaminaInfo.ReadRetry"]

    # 读取失败只会在 Read/ReadRetry 之间循环，绝不会触碰点击分支
    assert "StaminaInfo.ClickHome" not in read_retry["next"]
    assert "StaminaInfo.ClickHomeRetry" not in read_retry["next"]


def test_stamina_pipeline_click_home_attempts_bounded_and_fails_fast() -> None:
    """回归：返回主页分支同样按次数收敛、快速失败，不残留长空转窗口。

    - ClickHomeRetry 闸门：按钮不匹配时最多重试 2 次（合计 3 次匹配/点击）；
    - hub 与 ClickHome 均 timeout=0：路由判定放弃/配置错误时立即失败，
      不再有原 60s（列表预算）与 20s（give-up 后）的空转等待。
    """
    pipeline = _stamina_pipeline()

    assert pipeline["StaminaInfo"]["timeout"] == 0
    assert pipeline["StaminaInfo.ClickHome"]["timeout"] == 0

    click_retry = pipeline["StaminaInfo.ClickHomeRetry"]
    assert click_retry["recognition"] == "DirectHit"
    assert click_retry["max_hit"] == 2
    assert click_retry["timeout"] == 0
    assert click_retry["next"] == ["StaminaInfo.ClickHome", "StaminaInfo.ClickHomeRetry"]

    # 返回分支不会触碰读取分支之外的路径
    assert "StaminaInfo.Read" not in click_retry["next"]
