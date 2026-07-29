import json

import pytest
from utils.params import (
    coerce_point,
    coerce_roi,
    extract_custom_param,
    is_int_value,
    merge_node_custom_param,
    parse_params,
)


class TestParseParamsEmpty:
    def test_none_returns_empty_dict(self) -> None:
        assert parse_params(None) == {}

    def test_empty_string_returns_empty_dict(self) -> None:
        assert parse_params("") == {}

    def test_none_with_required_raises(self) -> None:
        with pytest.raises(ValueError, match="参数为空"):
            parse_params(None, "key")


class TestParseParamsDict:
    def test_simple_json(self) -> None:
        result = parse_params('{"a": 1}')
        assert result == {"a": 1}

    def test_nested_json(self) -> None:
        result = parse_params('{"a": {"b": 2}}')
        assert result == {"a": {"b": 2}}

    def test_multilayer_escaped_json(self) -> None:
        inner = json.dumps({"a": 1})
        outer = json.dumps(inner)
        result = parse_params(outer)
        assert result == {"a": 1}

    def test_multilayer_escaped_json_non_object(self) -> None:
        outer = json.dumps("[1, 2, 3]")
        with pytest.raises(ValueError, match="参数必须是对象"):
            parse_params(outer)


class TestParseParamsValidation:
    def test_non_object_raises(self) -> None:
        with pytest.raises(ValueError, match="参数必须是对象"):
            parse_params("[1, 2, 3]")

    def test_missing_required_key_raises(self) -> None:
        with pytest.raises(ValueError, match="缺少必填字段"):
            parse_params('{"a": 1}', "b")

    def test_required_keys_present(self) -> None:
        result = parse_params('{"a": 1, "b": 2}', "a", "b")
        assert result == {"a": 1, "b": 2}

    def test_invalid_json_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="参数必须是对象"):
            parse_params("not json at all")


class TestExtractCustomParam:
    def test_none_returns_empty(self) -> None:
        assert extract_custom_param(None) == {}

    def test_node_data_not_dict(self) -> None:
        assert extract_custom_param([]) == {}
        assert extract_custom_param("string") == {}
        assert extract_custom_param(42) == {}

    def test_well_formed_node(self) -> None:
        node = {"action": {"type": "Custom", "param": {"custom_action": "X", "custom_action_param": {"a": 1}}}}
        assert extract_custom_param(node) == {"a": 1}

    def test_missing_action(self) -> None:
        assert extract_custom_param({"recognition": "DirectHit"}) == {}

    def test_action_not_dict(self) -> None:
        assert extract_custom_param({"action": "bad"}) == {}

    def test_missing_param(self) -> None:
        assert extract_custom_param({"action": {"type": "Custom"}}) == {}

    def test_param_not_dict(self) -> None:
        assert extract_custom_param({"action": {"param": "bad"}}) == {}

    def test_missing_custom_action_param(self) -> None:
        assert extract_custom_param({"action": {"param": {"custom_action": "X"}}}) == {}

    def test_custom_action_param_not_dict(self) -> None:
        assert extract_custom_param({"action": {"param": {"custom_action_param": "bad"}}}) == {}


class _MockContext:
    """Minimal mock for maa.context.Context used by merge_node_custom_param tests."""

    def __init__(self, node_data: dict[str, object] | None) -> None:
        self._node_data = node_data
        self.overrides: list[tuple[str, dict[str, object]]] = []

    def get_node_data(self, name: str) -> dict[str, object] | None:
        return self._node_data

    def override_pipeline(self, config: dict[str, object]) -> None:
        self.overrides.append(tuple(config.items())[0])  # type: ignore[arg-type]


class TestMergeNodeCustomParam:
    def test_preserves_custom_action_and_merges_field(self) -> None:
        node = {"action": {"type": "Custom", "param": {"custom_action": "X", "custom_action_param": {"a": 1}}}}
        ctx = _MockContext(node)
        merge_node_custom_param(ctx, "Node", {"b": 2})
        assert len(ctx.overrides) == 1
        name, payload = ctx.overrides[0]
        assert name == "Node"
        param = payload["action"]["param"]  # type: ignore[index]
        assert param["custom_action"] == "X"
        assert param["custom_action_param"] == {"a": 1, "b": 2}

    def test_creates_custom_action_param_when_absent(self) -> None:
        node = {"action": {"type": "Custom", "param": {"custom_action": "X"}}}
        ctx = _MockContext(node)
        merge_node_custom_param(ctx, "Node", {"target": 5})
        _, payload = ctx.overrides[0]
        param = payload["action"]["param"]  # type: ignore[index]
        assert param["custom_action"] == "X"
        assert param["custom_action_param"] == {"target": 5}

    def test_preserves_other_param_fields(self) -> None:
        node = {
            "action": {
                "type": "Custom",
                "param": {"custom_action": "X", "custom_action_param": {"a": 1}, "extra": True},
            }
        }
        ctx = _MockContext(node)
        merge_node_custom_param(ctx, "Node", {"b": 2})
        _, payload = ctx.overrides[0]
        param = payload["action"]["param"]  # type: ignore[index]
        assert param["extra"] is True
        assert param["custom_action_param"] == {"a": 1, "b": 2}

    def test_empty_node_data(self) -> None:
        ctx = _MockContext(None)
        merge_node_custom_param(ctx, "Node", {"remaining": 3})
        _, payload = ctx.overrides[0]
        param = payload["action"]["param"]  # type: ignore[index]
        assert param["custom_action_param"] == {"remaining": 3}

    def test_overwrites_existing_key_with_update(self) -> None:
        node = {"action": {"param": {"custom_action": "X", "custom_action_param": {"target": 1, "other": "keep"}}}}
        ctx = _MockContext(node)
        merge_node_custom_param(ctx, "Node", {"target": 5})
        _, payload = ctx.overrides[0]
        param = payload["action"]["param"]  # type: ignore[index]
        assert param["custom_action_param"] == {"target": 5, "other": "keep"}

    def test_action_not_dict_creates_empty_param(self) -> None:
        ctx = _MockContext({"action": "bad", "recognition": "DirectHit"})
        merge_node_custom_param(ctx, "Node", {"x": 1})
        _, payload = ctx.overrides[0]
        action = payload["action"]  # type: ignore[index]
        assert action["param"]["custom_action_param"] == {"x": 1}  # type: ignore[index]

    def test_param_not_dict_preserves_action_type(self) -> None:
        ctx = _MockContext({"action": {"type": "Custom", "param": "bad"}})
        merge_node_custom_param(ctx, "Node", {"y": 2})
        _, payload = ctx.overrides[0]
        action = payload["action"]  # type: ignore[index]
        assert action["type"] == "Custom"
        assert action["param"]["custom_action_param"] == {"y": 2}  # type: ignore[index]

    def test_preserves_action_type_and_other_action_fields(self) -> None:
        node = {"action": {"type": "Custom", "param": {"custom_action": "X", "custom_action_param": {"a": 1}}}}
        ctx = _MockContext(node)
        merge_node_custom_param(ctx, "Node", {"b": 2})
        _, payload = ctx.overrides[0]
        action = payload["action"]  # type: ignore[index]
        assert action["type"] == "Custom"
        param = action["param"]  # type: ignore[index]
        assert param["custom_action"] == "X"
        assert param["custom_action_param"] == {"a": 1, "b": 2}

    def test_param_not_dict_preserves_action_level_fields(self) -> None:
        ctx = _MockContext({"action": {"type": "Custom", "param": "bad", "extra": "keep"}})
        merge_node_custom_param(ctx, "Node", {"y": 2})
        _, payload = ctx.overrides[0]
        action = payload["action"]  # type: ignore[index]
        assert action["type"] == "Custom"
        assert action["extra"] == "keep"

    def test_strict_raises_when_node_missing(self) -> None:
        ctx = _MockContext(None)
        with pytest.raises(ValueError, match="节点 Missing 不存在"):
            merge_node_custom_param(ctx, "Missing", {"x": 1}, strict=True)

    def test_strict_raises_when_action_not_dict(self) -> None:
        ctx = _MockContext({"action": "bad"})
        with pytest.raises(ValueError, match="action 字段非 dict"):
            merge_node_custom_param(ctx, "Node", {"x": 1}, strict=True)

    def test_strict_raises_when_param_not_dict(self) -> None:
        ctx = _MockContext({"action": {"type": "Custom", "param": "bad"}})
        with pytest.raises(ValueError, match="action.param 字段非 dict"):
            merge_node_custom_param(ctx, "Node", {"x": 1}, strict=True)


class TestCoerceRoi:
    def test_valid_4_int_list(self) -> None:
        assert coerce_roi([1, 2, 3, 4], [9, 9, 9, 9], "X") == [1, 2, 3, 4]

    def test_valid_4_float_list(self) -> None:
        assert coerce_roi([1.0, 2.5, 3.0, 4.0], [9, 9, 9, 9], "X") == [1, 2, 3, 4]

    def test_valid_tuple(self) -> None:
        assert coerce_roi((1, 2, 3, 4), [9, 9, 9, 9], "X") == [1, 2, 3, 4]

    def test_bool_rejected(self) -> None:
        assert coerce_roi([True, False, True, False], [9, 9, 9, 9], "X") == [9, 9, 9, 9]

    def test_short_list_falls_back(self) -> None:
        assert coerce_roi([1, 2, 3], [9, 9, 9, 9], "X") == [9, 9, 9, 9]

    def test_long_list_falls_back(self) -> None:
        assert coerce_roi([1, 2, 3, 4, 5], [9, 9, 9, 9], "X") == [9, 9, 9, 9]

    def test_none_falls_back(self) -> None:
        assert coerce_roi(None, [9, 9, 9, 9], "X") == [9, 9, 9, 9]

    def test_str_falls_back(self) -> None:
        assert coerce_roi("1,2,3,4", [9, 9, 9, 9], "X") == [9, 9, 9, 9]

    def test_non_numeric_falls_back(self) -> None:
        assert coerce_roi([1, 2, "3", 4], [9, 9, 9, 9], "X") == [9, 9, 9, 9]


class TestCoercePoint:
    def test_valid_2_int_tuple(self) -> None:
        assert coerce_point((1086, 470), (0, 0), "X", "y") == (1086, 470)

    def test_valid_2_int_list(self) -> None:
        assert coerce_point([100, 200], (0, 0), "X", "y") == (100, 200)

    def test_valid_2_float(self) -> None:
        assert coerce_point([1.5, 2.5], (0, 0), "X", "y") == (1, 2)

    def test_bool_rejected(self) -> None:
        assert coerce_point([True, False], (0, 0), "X", "y") == (0, 0)

    def test_wrong_length_falls_back(self) -> None:
        assert coerce_point([1, 2, 3], (10, 20), "X", "y") == (10, 20)

    def test_short_list_falls_back(self) -> None:
        assert coerce_point([1], (10, 20), "X", "y") == (10, 20)

    def test_none_falls_back(self) -> None:
        assert coerce_point(None, (10, 20), "X", "y") == (10, 20)

    def test_non_numeric_falls_back(self) -> None:
        assert coerce_point([1, "x"], (10, 20), "X", "y") == (10, 20)


class TestIsIntValue:
    def test_int_true(self) -> None:
        assert is_int_value(1) is True

    def test_int_zero(self) -> None:
        assert is_int_value(0) is True

    def test_int_negative(self) -> None:
        assert is_int_value(-5) is True

    def test_bool_true_rejected(self) -> None:
        assert is_int_value(True) is False

    def test_bool_false_rejected(self) -> None:
        assert is_int_value(False) is False

    def test_float_rejected(self) -> None:
        assert is_int_value(1.5) is False

    def test_str_rejected(self) -> None:
        assert is_int_value("1") is False

    def test_none_rejected(self) -> None:
        assert is_int_value(None) is False

    def test_list_rejected(self) -> None:
        assert is_int_value([1]) is False
