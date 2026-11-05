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
