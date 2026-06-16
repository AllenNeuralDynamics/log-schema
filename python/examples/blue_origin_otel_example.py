import logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

from log_schema import setup_logging

# Factory to create tracers - outputs to console at the end of the program
provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("Blue Origin Rocket Tracer")

# Setup logging (supports open telemetry trace context)
setup_logging()

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
    logging.info("checking crew")


# Example of using the tracer as a context manager to automatically create spans
@tracer.start_as_current_span("pre_launch_procedures")
def pre_launch_procedures():
    fuel_rocket()
    # Example of Nested spans - all will be children of pre_launch_procedures span
    with tracer.start_as_current_span("pre_launch_checks"):
        check_fuel_line()
        check_o_rings()
        check_crew()
    logging.info("all systems go")


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