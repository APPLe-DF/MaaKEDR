import json

import pytest
from utils.params import extract_custom_param, parse_params


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
