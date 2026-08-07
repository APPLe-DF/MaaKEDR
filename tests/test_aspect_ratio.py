from custom.sink.aspect_ratio import RATIO_TOLERANCE, is_aspect_ratio_16x9


class TestIsAspectRatio16x9:
    def test_720p(self) -> None:
        assert is_aspect_ratio_16x9(1280, 720)

    def test_1080p(self) -> None:
        assert is_aspect_ratio_16x9(1920, 1080)

    def test_1440p(self) -> None:
        assert is_aspect_ratio_16x9(2560, 1440)

    def test_portrait_rejected(self) -> None:
        assert not is_aspect_ratio_16x9(720, 1280)

    def test_4x3_rejected(self) -> None:
        assert not is_aspect_ratio_16x9(1024, 768)

    def test_zero_rejected(self) -> None:
        assert not is_aspect_ratio_16x9(0, 0)

    def test_negative_rejected(self) -> None:
        assert not is_aspect_ratio_16x9(-1280, -720)

    def test_tolerance_edge(self) -> None:
        # 恰好处于容差边界内时应通过
        width = 16 * 100
        height = 9 * 100
        assert is_aspect_ratio_16x9(width, height)

    def test_tolerance_upper_bound(self) -> None:
        # 略超容差（RATIO_TOLERANCE=0.02）时应拒绝
        width = 16 * 100
        height = 9 * 100 - int(9 * 100 * RATIO_TOLERANCE * 2)
        assert not is_aspect_ratio_16x9(width, height)
