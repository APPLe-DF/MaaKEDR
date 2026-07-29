import json

import pytest
from utils.params import parse_params


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

    def test_invalid_json_returns_raw_string_then_raises(self) -> None:
        with pytest.raises(ValueError, match="参数必须是对象"):
            parse_params("not json at all")
