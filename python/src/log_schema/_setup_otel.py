import logging
from typing import Any, Mapping

from pydantic import BaseModel

from ._setup_base import setup_logging


def setup_logging_otel(
    resource: dict | None = None,
    model: dict | BaseModel | None = None,
    include_trace_context: bool = True,
) -> None:
    """"""

    # Lazy import to make opentelemetry optional for users who don't need it
    from opentelemetry import trace
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider as TraceProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    OTLP_ENDPOINT = "http://localhost:4317"

    ################################################################################
    #
    #   Tracing Setup
    #
    ################################################################################

    # Setup tracing
    trace_provider = TraceProvider(resource=Resource.create(resource or {}))
    trace_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(trace_provider)

    ################################################################################
    #
    #   Logging Setup
    #
    ################################################################################

    logging_provider = LoggerProvider(resource=Resource.create(resource or {}))
    logging_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=OTLP_ENDPOINT, insecure=True))
    )
    set_logger_provider(logging_provider)

    # Custom wrapper to attach static fields defined in model
    class StaticFieldsHandler(LoggingHandler):
        """LoggingHandler that stamps a fixed attribute set onto every record."""

        def __init__(
            self,
            *,
            static_fields: Mapping[str, Any],
            level: int = logging.NOTSET,
            logger_provider=None,
        ):
            super().__init__(level=level, logger_provider=logger_provider)
            self._static_fields = dict(static_fields)  # copy: caller can't mutate later

        def _translate(self, record: logging.LogRecord):
            otel_record = super()._translate(record)
            for key, value in self._static_fields.items():
                otel_record.attributes.setdefault(key, value)
            return otel_record

    combined_model = (
        model.model_dump() if isinstance(model, BaseModel) else model or {} | resource or {}
    )

    # Setup base logging (console)
    setup_logging(model=combined_model)

    # Attach otel logging handler to root logger
    logging.getLogger().addHandler(
        StaticFieldsHandler(
            static_fields=model.model_dump() if isinstance(model, BaseModel) else model or {},
            logger_provider=logging_provider,
        )
    )
