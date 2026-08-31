from __future__ import annotations

import custom.action.farm_resources as farm_action
from custom.action.farm_resources import _next_target


class TestReduceBattleCountNextTarget:
    """回归：ReduceBattleCount 的目标次数必须以屏幕 OCR 当前次数为准。"""

    def test_second_farm_run_resyncs_from_stale_tracked(self) -> None:
        """二次「剩余体力刷取」时次数已重置为 6，而 tracked 残留为 1（上一轮耗尽）。

        旧实现直接使用残留 tracked（1）判定「已到最小」返回失败，导致本轮一场未打；
        新实现见到有效读数（6）后应重新校准：6 → 5。
        """
        assert _next_target(current_count=6, tracked=1) == 5

    def test_ocr_count_reduces_by_one(self) -> None:
        assert _next_target(current_count=4, tracked=None) == 3

    def test_ocr_count_one_cannot_reduce(self) -> None:
        assert _next_target(current_count=1, tracked=2) is None

    def test_ocr_failure_falls_back_to_tracked(self) -> None:
        assert _next_target(current_count=-1, tracked=3) == 2

    def test_ocr_failure_tracked_at_min_stops(self) -> None:
        assert _next_target(current_count=-1, tracked=1) is None

    def test_ocr_failure_no_tracked_defaults_then_reduces(self) -> None:
        assert _next_target(current_count=-1, tracked=None) == 5

    def test_ocr_failure_tracked_unbounded_still_decrements(self) -> None:
        # 有界性：即使读不到 OCR，跟踪值也只会单调递减（每次调用最多 -1）
        first = _next_target(current_count=-1, tracked=6)
        assert first == 5
        assert _next_target(current_count=-1, tracked=first) == 4


class TestResetTarget:
    """回归：进入关卡界面（SetBattleCount 必然先执行）须清零跨任务残留的 _target。"""

    def test_stale_tracked_cleared_on_stage_entry(self) -> None:
        """上一任务清空体力结束后 _target 残留为 1；进入新任务后必须清零。

        若不重置，本任务首次减次的 OCR 失败回退会命中该残留值（1），
        被误判「已到最小」返回失败 → on_error 走 NoStamina 退出（0 场）；
        清零后回退走 _DEFAULT_TARGET：6 → 5，与资源刷取/剩余体力刷取
        均可正常继续减次。
        """
        farm_action._target = 1  # 模拟上一任务耗尽的残留
        farm_action._reset_target()
        assert farm_action._target is None
        assert _next_target(current_count=-1, tracked=farm_action._target) == 5
