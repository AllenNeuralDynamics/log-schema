import io
import json
import logging
from functools import partial
from unittest.mock import Mock

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.util._once import Once
from pydantic import BaseModel

from log_schema import DefaultFormatter, setup_logging_otel
from tests.helpers.assertions import extract_log_entry
from tests.helpers.configs import ConfigBuilder

################################################################################
#
#   Utility functions for tests
#
################################################################################


class ResourceModel(BaseModel):
    service_name: str = "my-app"


def _reset_global_tracer_provider():
    # set_tracer_provider only works once per process; OTel's own test utils reset it like this.
    trace._TRACER_PROVIDER_SET_ONCE = Once()
    trace._TRACER_PROVIDER = None


@pytest.fixture(autouse=True)
def otlp_exporter(monkeypatch):
    """Swaps the OTLP gRPC exporter (network boundary) for an in-memory one."""
    _reset_global_tracer_provider()
    factory = Mock(return_value=InMemorySpanExporter())
    monkeypatch.setattr(
        "opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter", factory
    )
    yield factory
    provider = trace.get_tracer_provider()
    if hasattr(provider, "shutdown"):
        provider.shutdown()
    _reset_global_tracer_provider()


def _finished_spans(otlp_exporter):
    trace.get_tracer_provider().force_flush()
    return otlp_exporter.return_value.get_finished_spans()


################################################################################
#
#   OTEL tests
#
################################################################################


def test_setup_logging_otel_logs_inside_span_include_trace_and_span_ids(capsys):
    """
    Tests: logs emitted inside a span
    Expect: the log entry to include the trace_id and span_id corresponding to the current span.
    """
    setup_logging_otel()
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("work") as span:
        logging.info("Test log message")
        context = span.get_span_context()

    log_entry = extract_log_entry(capsys)

    assert log_entry["trace_id"] == format(context.trace_id, "032x")
    assert log_entry["span_id"] == format(context.span_id, "016x")


def test_setup_logging_otel_logs_outside_span_have_no_trace_context(capsys):
    """
    Tests: logs emitted outside a span
    Expect: the log entry to not include trace_id and span_id.
    """
    setup_logging_otel()

    logging.info("Test log message")

    log_entry = extract_log_entry(capsys)

    assert "trace_id" not in log_entry
    assert "span_id" not in log_entry


def test_setup_logging_otel_include_trace_context_false_omits_ids(capsys):
    """
    Tests: a log emitted inside a span with include_trace_context set to False
    Expect: the log entry to not include trace_id and span_id.
    """
    setup_logging_otel(include_trace_context=False)
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("work"):
        logging.info("Test log message")

    log_entry = extract_log_entry(capsys)

    assert "trace_id" not in log_entry
    assert "span_id" not in log_entry


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param("log_schema.DefaultFormatter", id="package path"),
        pytest.param("log_schema._setup_base.DefaultFormatter", id="module path"),
        pytest.param(DefaultFormatter, id="class object"),
    ],
)
def test_setup_logging_otel_custom_config_default_formatter_gets_trace_context(capsys, factory):
    """
    Tests: a custom config with the default formatter
    Expect: the log entry to include trace_id - injected to formatter.
    """
    config = ConfigBuilder().get_config_dict(None, False)
    config["formatters"]["default"]["()"] = factory

    setup_logging_otel(config=config)
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("work"):
        logging.info("Test log message")

    assert "trace_id" in extract_log_entry(capsys)


def test_setup_logging_otel_custom_config_non_default_formatter_unchanged(capsys):
    """
    Tests: a custom config with a non-default formatter
    Expect: the log entry to remain unchanged and not include trace_id.
    """
    setup_logging_otel(config=ConfigBuilder().get_config_dict(None, False))
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("work"):
        logging.info("Test log message")

    assert capsys.readouterr().out.strip() == "Test log message"


def test_setup_logging_otel_does_not_mutate_caller_config():
    """
    Tests: that the caller's config is not mutated by setup_logging_otel.
    Expect: the config remains unchanged after calling setup_logging_otel.
    """
    config = ConfigBuilder().get_config_dict("default", False)

    setup_logging_otel(config=config, include_trace_context=False)

    assert config == ConfigBuilder().get_config_dict("default", False)


def test_setup_logging_otel_model_and_resource_fields_in_logs(capsys):
    """
    Tests model and resource are both added as static log fields.
    Expect: resource wins over model on overlapping keys.
    """
    setup_logging_otel(
        resource={"service.name": "my-app", "env": "from-resource"},
        model={"team": "platform", "env": "from-model"},
    )

    logging.info("Test log message")

    log_entry = extract_log_entry(capsys)

    assert log_entry["service.name"] == "my-app"
    assert log_entry["team"] == "platform"
    assert log_entry["env"] == "from-resource"


@pytest.mark.parametrize(
    "resource, key",
    [
        pytest.param({"service.name": "my-app"}, "service.name", id="dict"),
        pytest.param(ResourceModel(), "service_name", id="pydantic model"),
    ],
)
def test_setup_logging_otel_exported_spans_have_resource(otlp_exporter, resource, key):
    """
    Tests: that the exported spans have the correct resource attributes.
    Expect: the span's resource attributes to match the provided resource.
    """
    setup_logging_otel(resource=resource)
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("work"):
        pass

    (span,) = _finished_spans(otlp_exporter)

    assert span.name == "work"
    assert span.resource.attributes[key] == "my-app"


def test_setup_logging_otel_exports_to_otlp_endpoint(otlp_exporter):
    """
    Tests: that setup_logging_otel correctly configures the OTLP endpoint.
    Expect: the OTLP exporter to use the specified endpoint.
    """
    setup_logging_otel(otlp_endpoint="http://collector:4317")

    assert otlp_exporter.call_args.kwargs["endpoint"] == "http://collector:4317"


def test_setup_logging_otel_console_exporter_prints_spans(monkeypatch):
    """
    Tests: that the ConsoleSpanExporter prints spans to the console.
    Expect: the span to be printed to the specified output buffer.
    """
    # ConsoleSpanExporter binds sys.stdout at import time, so capture fixtures can't see it.
    buffer = io.StringIO()
    monkeypatch.setattr(
        "opentelemetry.sdk.trace.export.ConsoleSpanExporter",
        partial(ConsoleSpanExporter, out=buffer),
    )
    setup_logging_otel(console_exporter=True)
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("console-span"):
        pass

    assert json.loads(buffer.getvalue())["name"] == "console-span"
