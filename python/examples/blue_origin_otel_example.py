import logging
from typing import Any, Mapping

from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

from log_schema import setup_logging, setup_logging_otel

# OTLP_ENDPOINT = "http://localhost:4317"
# SERVICE_NAME = "blue_origin_rocket"
# resource = Resource.create(
#     {
#         "service.name": SERVICE_NAME,
#         "service.version": "0.1.0",
#         "deployment.environment": "eng-logtools",
#     }
# )


# def build_tracer_provider():
#     provider = TracerProvider(resource=resource)

#     # insecure=True (minikube testing, local port forward has no TLS)
#     exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)

#     provider.add_span_processor(BatchSpanProcessor(exporter))
#     provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

#     return provider


# provider = build_tracer_provider()
# trace.set_tracer_provider(provider)
# tracer = trace.get_tracer("Blue Origin Rocket Tracer")

# # Setup logging (supports open telemetry trace context)
# logger_provider = LoggerProvider(resource=resource)
# logger_provider.add_log_record_processor(
#     BatchLogRecordProcessor(OTLPLogExporter(endpoint=OTLP_ENDPOINT, insecure=True))
# )
# set_logger_provider(logger_provider)

# setup_logging()  # JSON console formatter + root=INFO



# class StaticFieldsHandler(LoggingHandler):
#     """LoggingHandler that stamps a fixed attribute set onto every record."""

#     def __init__(
#         self,
#         *,
#         static_fields: Mapping[str, Any],
#         level: int = logging.NOTSET,
#         logger_provider=None,
#     ):
#         super().__init__(level=level, logger_provider=logger_provider)
#         self._static_fields = dict(static_fields)  # copy: caller can't mutate later

#     def _translate(self, record: logging.LogRecord):
#         otel_record = super()._translate(record)
#         for key, value in self._static_fields.items():
#             otel_record.attributes.setdefault(key, value)
#         return otel_record


# # logging.getLogger().addHandler(LoggingHandler(logger_provider=logger_provider))
# logging.getLogger().addHandler(
#     StaticFieldsHandler(
#         logger_provider=logger_provider,
#         static_fields={"banana": "allergic", "oranges": "most yummy"},
#     )
# )

resource = {
    "service.name": "blue-origin-setup-test",
    "service.version": "1.1.1",
}

model = {
    "teletubby1": "po",
    "teletubby2": "laa-laa",
}

tracer = trace.get_tracer("Blue Origin Rocket Tracer")


setup_logging_otel(model=model, resource=resource) 

################################################################################
#
#   Rocket Launch Code
#
################################################################################


def fuel_rocket():
    logging.info(
        "fueling rocket - override trace/span id test",
        extra={"trace_id": "1234", "span_id": "5678"},
    )
    logging.info("fueling rocket")


def check_fuel_line():
    logging.info("checking fuel lines")


def check_o_rings():
    logging.info("checking O-rings")


def check_crew():
    logging.info("checking crew", extra={"banana":"SUPER BANANA ERASES ALL"})


# Example of using the tracer as a context manager to automatically create spans
@tracer.start_as_current_span("pre_launch_procedures")
def pre_launch_procedures():
    fuel_rocket()
    # Example of Nested spans - all will be children of pre_launch_procedures span
    with tracer.start_as_current_span("pre_launch_checks"):
        check_fuel_line()
        check_o_rings()
        check_crew()
    logging.info("all systems go", extra={"testing_extra_fields": "cheeHOO"})


@tracer.start_as_current_span("launch_sequence")
def launch_rocket():
    try:
        # Example of adding events to a span
        current_span = trace.get_current_span()
        current_span.add_event("engines ignited")
        current_span.add_event("helmets equipped")
        raise Exception("blue origin rocket exploded")
    except Exception as ex:
        # Example of recording an exception and setting error status on the span
        current_span = trace.get_current_span()
        current_span.set_status(trace.status.Status(trace.status.StatusCode.ERROR))
        current_span.record_exception(ex)
        logging.error("rocket exploded")


################################################################################
#
#   Driver Code
#
################################################################################

pre_launch_procedures()
launch_rocket()

logging.info("Test done - no span/trace")
