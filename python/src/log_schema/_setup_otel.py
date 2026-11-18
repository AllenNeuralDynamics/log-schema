from __future__ import annotations

from pydantic import BaseModel

from ._setup_base import (
    DefaultFormatter,
    _get_default_config,
    _model_to_fields,
    _resolve_formatter_factory,
    setup_logging,
)


def otel_log_handler(endpoint: str | None = None, protocol: str = "grpc"):
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, LogRecordExporter

    exporter: LogRecordExporter
    if protocol == "grpc":
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
            OTLPLogExporter as GrpcLogExporter,
        )

        exporter = GrpcLogExporter(endpoint=endpoint, insecure=True)
    elif protocol == "http":
        from opentelemetry.exporter.otlp.proto.http._log_exporter import (
            OTLPLogExporter as HttpLogExporter,
        )

        exporter = HttpLogExporter(endpoint=endpoint)
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")

    # Not registered globally: the handler holds its own provider, so repeated setup doesn't warn.
    logging_provider = LoggerProvider()
    logging_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    return LoggingHandler(logger_provider=logging_provider)


def setup_logging_otel(
    resource: dict | BaseModel = {},
    config: dict | None = None,
    model: dict | BaseModel = {},
    include_trace_context: bool = True,
    console_exporter: bool = False,
    otlp_endpoint: str = "http://localhost:4317",
) -> None:
    # Lazy import to make opentelemetry optional for users who don't need it
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider as TraceProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    ################################################################################
    #
    #   Tracing Setup
    #
    ################################################################################
    resource = _model_to_fields(resource)

    # Setup tracing
    trace_provider = TraceProvider(resource=Resource.create(resource))
    trace_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)

    if console_exporter:
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

        trace_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(trace_provider)

    ###

    model_dict = _model_to_fields(model)
    combined_model = model_dict | resource

    source_config = config if config is not None else _get_default_config()
    config = source_config.copy()

    ###

    formatters = source_config.get("formatters", {})
    if isinstance(formatters, dict):
        updated_formatters = formatters.copy()
        for formatter_name, formatter_config in formatters.items():
            if not isinstance(formatter_config, dict):
                continue
            formatter_factory = _resolve_formatter_factory(formatter_config.get("()"))
            if isinstance(formatter_factory, type) and issubclass(
                formatter_factory, DefaultFormatter
            ):
                updated_formatter_config = formatter_config.copy()
                updated_formatter_config["include_trace_context"] = include_trace_context
                updated_formatters[formatter_name] = updated_formatter_config
        config["formatters"] = updated_formatters

    ###

    setup_logging(model=combined_model, config=config)
