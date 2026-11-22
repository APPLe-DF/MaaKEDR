from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast


def _claim_rewards_pipeline() -> dict[str, Any]:
    pipeline_path = Path(__file__).parents[1] / "resource" / "base" / "pipeline" / "claim_rewards.json"
    return cast(dict[str, Any], json.loads(pipeline_path.read_text(encoding="utf-8")))


def _dispatch_redeploy_no_override() -> dict[str, Any]:
    tasks_path = Path(__file__).parents[1] / "tasks" / "claim_rewards.json"
    tasks = cast(dict[str, Any], json.loads(tasks_path.read_text(encoding="utf-8")))
    for case in tasks["option"]["dispatch_redeploy"]["cases"]:
        if case["name"] == "No":
            return cast(dict[str, Any], case["pipeline_override"])
    raise AssertionError("dispatch_redeploy=No case not found")


def test_claim_rewards_dispatch_entry_has_no_retry_click() -> None:
    """回归 #86：面板展开动画期间不得用同一红点判据再次点击入口。"""
    pipeline = _claim_rewards_pipeline()

    assert "DispatchClaim.RetryClick" not in pipeline

    dangling = [
        f"{node} -> {ref}"
        for node, definition in pipeline.items()
        if isinstance(definition, dict)
        for ref in [*definition.get("next", []), *definition.get("on_error", [])]
        if isinstance(ref, str) and ref.removeprefix("[JumpBack]") == "DispatchClaim.RetryClick"
    ]
    assert dangling == []


def test_claim_rewards_dispatch_start_is_bounded_and_fails_loudly() -> None:
    """入口点击未生效时必须有界失败，且不得被 MainHub 反复重入。"""
    start = _claim_rewards_pipeline()["DispatchClaim.Start"]

    assert start["max_hit"] == 1
    assert start["timeout"] == 10000
    assert start["next"] == [
        "DispatchClaim.ClaimButton",
        "DispatchClaim.Exit",
        "[JumpBack]Common.CheckItemObtained",
    ]


def test_claim_rewards_dispatch_start_clicks_entry_icon() -> None:
    """回归：红点 box 仅 18×18 且含外圈，Click 必须偏移到入口图标上，不能点在红点边缘。"""
    start = _claim_rewards_pipeline()["DispatchClaim.Start"]
    action = start["action"]

    assert action["type"] == "Click"
    assert action["param"]["target_offset"] == [24, 17, -5, -7]

    # 实机 ColorMatch 命中框约 [908,303,18,18]；偏移后的点击矩形应落在白色入口图标内
    box_x, box_y, box_w, box_h = 908, 303, 18, 18
    offset_x, offset_y, offset_w, offset_h = action["param"]["target_offset"]
    target = (box_x + offset_x, box_y + offset_y, box_w + offset_w, box_h + offset_h)
    assert target == (932, 320, 13, 11)
    assert target[0] >= 930 and target[0] + target[2] <= 1014
    assert target[1] >= 312 and target[1] + target[3] <= 341


def test_claim_rewards_dispatch_recovery_loop_is_bounded() -> None:
    """「关闭」未出现时先关物品弹窗、再回头领一次，并由 max_hit 封顶。"""
    pipeline = _claim_rewards_pipeline()

    assert pipeline["DispatchClaim.ClaimButton"]["next"] == [
        "[JumpBack]Common.CheckItemObtained",
        "DispatchClaim.RedeployConfirm",
    ]
    assert pipeline["DispatchClaim.RedeployConfirm"]["next"] == [
        "[JumpBack]Common.CheckItemObtained",
        "DispatchClaim.Exit",
        "DispatchClaim.ClaimButton",
    ]
    assert pipeline["DispatchClaim.ClaimButton"]["max_hit"] == 4


def test_claim_rewards_dispatch_item_popup_keeps_jumpback_in_redeploy_off_override() -> None:
    """回归：dispatch_redeploy=No 覆盖曾漏掉 [JumpBack]，物品弹窗命中叶子后会跳过 Exit。"""
    override = _dispatch_redeploy_no_override()

    assert override["DispatchClaim.ClaimButton"]["next"] == [
        "[JumpBack]Common.CheckItemObtained",
        "DispatchClaim.RedeployConfirm",
        "DispatchClaim.Exit",
    ]
