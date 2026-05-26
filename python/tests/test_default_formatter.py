import json
import logging
from datetime import datetime, timezone

import pytest

from schlog.main import DefaultFormatter
from tests.logging_model_builders import LogConfigModel


def test_default_formatter_sets_expected_default_fields():
    formatter = DefaultFormatter()
    record = _make_record("hello")
    payload = _format_to_dict(formatter, record)

    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
    assert "timestamp" in payload
    assert "asctime" not in payload
    assert "levelname" not in payload


def test_default_formatter_preserves_custom_rename_fields():
    formatter = DefaultFormatter(rename_fields={"levelname": "severity"})
    record = _make_record("hello")
    payload = _format_to_dict(formatter, record)

    assert payload["message"] == "hello"
    assert payload["severity"] == "INFO"
    assert "level" not in payload


def test_default_formatter_preserves_custom_fmt_and_style():
    formatter = DefaultFormatter(fmt="%(message)s", style="%")
    record = _make_record("hello")
    payload = _format_to_dict(formatter, record)

    assert payload["message"] == "hello"


def test_default_formatter_adds_static_fields_from_dict_model():
    formatter = DefaultFormatter(model={"app_name": "my_app", "env": "production"})
    record = _make_record("hello")
    payload = _format_to_dict(formatter, record)

    assert payload["app_name"] == "my_app"
    assert payload["env"] == "production"


def test_default_formatter_adds_static_fields_from_pydantic_model():
    formatter = DefaultFormatter(model=LogConfigModel())
    record = _make_record("hello")
    payload = _format_to_dict(formatter, record)

    assert payload["app_name"] == "my_app"
    assert payload["env"] == "production"


def test_default_formatter_invalid_model_type_raises_type_error():
    with pytest.raises(TypeError):
        DefaultFormatter(model=123)


def test_default_formatter_does_not_override_existing_static_fields():
    formatter = DefaultFormatter(
        model={"env": "from_model", "app_name": "from_model"},
        static_fields={"env": "from_config", "fixed": "yes"},
    )
    record = _make_record("hello")
    payload = _format_to_dict(formatter, record)

    assert payload["env"] == "from_config"
    assert payload["fixed"] == "yes"
    assert "app_name" not in payload


def test_default_formatter_format_time_uses_utc_and_expected_format():
    formatter = DefaultFormatter()
    record = _make_record("hello")
    record.created = 0.0

    timestamp = formatter.formatTime(record)

    assert timestamp == "1970-01-01T00:00:00.000000Z"
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    assert parsed.tzinfo == timezone.utc


################################################################################
#
#   Utility functions for tests
#
################################################################################


def _make_record(message: str, level: int = logging.INFO, **extra) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test_logger",
        level=level,
        pathname=__file__,
        lineno=123,
        msg=message,
        args=(),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def _format_to_dict(formatter: DefaultFormatter, record: logging.LogRecord) -> dict:
    output = formatter.format(record)
    return json.loads(output)
