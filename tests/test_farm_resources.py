from __future__ import annotations

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
