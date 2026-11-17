import json
import logging
from datetime import datetime, timezone

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from log_schema import DefaultFormatter
from tests.helpers.models import LogConfigModel

################################################################################
#
#   Utility functions for tests
#
################################################################################


@pytest.fixture(scope="module", autouse=True)
def _tracer_provider():
    # set_tracer_provider can only be called once per process; ignore if already set.
    try:
        trace.set_tracer_provider(TracerProvider())
    except RuntimeError:
        pass
    return trace.get_tracer_provider()


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


################################################################################
#
#   Tests for DefaultFormatter
#
################################################################################


def test_default_formatter_sets_expected_default_fields():
    """
    Tests: that the default formatter sets the expected default fields.
    Expect: the payload to include message, level, and timestamp, but not asctime or levelname.
    """
    formatter = DefaultFormatter()
    record = _make_record("hello")
    payload = _format_to_dict(formatter, record)

    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
    assert "timestamp" in payload
    assert "asctime" not in payload
    assert "levelname" not in payload


def test_default_formatter_adds_static_fields_from_dict_model():
    """
    Tests: that the default formatter adds static fields from a dictionary model.
    Expect: the payload to include the fields from the model.
    """
    formatter = DefaultFormatter(model={"app_name": "my_app", "env": "production"})
    record = _make_record("hello")
    payload = _format_to_dict(formatter, record)

    assert payload["app_name"] == "my_app"
    assert payload["env"] == "production"


def test_default_formatter_adds_static_fields_from_pydantic_model():
    """
    Tests: that the default formatter adds static fields from a Pydantic model.
    Expect: the payload to include the fields from the model.
    """
    formatter = DefaultFormatter(model=LogConfigModel())
    record = _make_record("hello")
    payload = _format_to_dict(formatter, record)

    assert payload["app_name"] == "my_app"
    assert payload["env"] == "production"


def test_default_formatter_invalid_model_type_raises_type_error():
    """
    Tests: that providing an invalid model type raises a TypeError.
    Expect: a TypeError to be raised when the model is not a dict or Pydantic model.
    """
    with pytest.raises(TypeError):
        DefaultFormatter(model=123)


def test_default_formatter_does_not_override_existing_static_fields():
    """
    Tests: that the default formatter does not override existing static fields.
    Expect: the payload to retain the values from static_fields and not include model fields.
    """
    formatter = DefaultFormatter(
        model={"env": "from_model", "app_name": "from_model"},
        static_fields={"env": "from_config", "fixed": "yes"},
    )
    record = _make_record("hello")
    payload = _format_to_dict(formatter, record)

    assert payload["env"] == "from_config"
    assert payload["fixed"] == "yes"
    assert "app_name" not in payload


def test_default_formatter_omits_trace_context_when_no_active_span():
    """
    Tests: that the default formatter omits trace context when there is no active span.
    Expect: the payload to not include trace_id and span_id.
    """
    formatter = DefaultFormatter()
    record = _make_record("hello")
    payload = _format_to_dict(formatter, record)

    assert "trace_id" not in payload
    assert "span_id" not in payload


def test_default_formatter_populates_trace_and_span_id_from_active_span():
    """
    Tests: that the default formatter populates trace_id and span_id from the active span.
    Expect: the payload to include the correct trace_id and span_id.
    """
    formatter = DefaultFormatter(include_trace_context=True)
    tracer = trace.get_tracer("test_default_formatter")
    with tracer.start_as_current_span("unit_span") as span:
        ctx = span.get_span_context()
        record = _make_record("hello")
        payload = _format_to_dict(formatter, record)

    assert payload["trace_id"] == format(ctx.trace_id, "032x")
    assert payload["span_id"] == format(ctx.span_id, "016x")


@pytest.mark.parametrize(
    "trace_id, span_id, expect_ids",
    [
        pytest.param(0x123, 0x456, True, id="both set"),
        pytest.param(0x123, 0, False, id="span_id zero"),
        pytest.param(0, 0x456, False, id="trace_id zero"),
        pytest.param(0, 0, False, id="both zero"),
    ],
)
def test_default_formatter_includes_context_ids_only_when_span_context_is_valid(
    trace_id, span_id, expect_ids
):
    """
    Tests: that the default formatter includes trace_id and span_id together or not at all.
    Expect: both ids only when both are non-zero (a valid OTel span context), otherwise neither.
    """
    formatter = DefaultFormatter(include_trace_context=True)
    context = trace.SpanContext(
        trace_id=trace_id,
        span_id=span_id,
        is_remote=False,
    )
    with trace.use_span(trace.NonRecordingSpan(context)):
        # The active span is set here, so the formatter should include trace context if valid.
        payload = _format_to_dict(formatter, _make_record("hello"))

    if expect_ids:
        assert payload["trace_id"] == format(trace_id, "032x")
        assert payload["span_id"] == format(span_id, "016x")
    else:
        assert "trace_id" not in payload
        assert "span_id" not in payload


def test_default_formatter_disable_trace_context_by_default():
    """
    Tests: that the default formatter does not include trace context by default.
    Expect: the payload to not include trace_id and span_id.
    """
    formatter = DefaultFormatter()
    tracer = trace.get_tracer("test_default_formatter")
    with tracer.start_as_current_span("unit_span"):
        record = _make_record("hello")
        payload = _format_to_dict(formatter, record)

    assert "trace_id" not in payload
    assert "span_id" not in payload


def test_default_formatter_format_time_uses_utc_and_expected_format():
    """
    Tests: that the default formatter formats the time in UTC with the expected ISO 8601 format.
    Expect: the timestamp to be in the format "YYYY-MM-DDTHH:MM:SS.ssssssZ" and in UTC.
    """
    formatter = DefaultFormatter()
    record = _make_record("hello")
    record.created = 0.0

    timestamp = formatter.formatTime(record)

    assert timestamp == "1970-01-01T00:00:00.000000Z"
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    assert parsed.tzinfo == timezone.utc
