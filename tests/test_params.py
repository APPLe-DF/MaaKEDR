import json

import pytest
from utils.params import extract_custom_param, merge_node_custom_param, parse_params


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
