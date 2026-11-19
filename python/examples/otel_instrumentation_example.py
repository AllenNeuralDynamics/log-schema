import logging

from opentelemetry import trace
from opentelemetry.semconv.attributes import server_attributes
from opentelemetry.trace import SpanContext, StatusCode, TraceFlags

from log_schema import setup_logging_otel

################################################################################
#
#   Setup Log/Trace
#
################################################################################


setup_logging_otel(console_exporter=True)  # console_exporter to see spans/traces in console
tracer = trace.get_tracer("Experiment-X")


################################################################################
#
#   Spans
#
################################################################################


# Creating Span
def initialize_camera_1():
    with tracer.start_as_current_span("initialize-camera-1"):
        logging.info("Initializing camera 1 - brr bzz bz")


# Creating Span with decorator
@tracer.start_as_current_span("initialize-camera-2")
def initialize_camera_2():
    logging.info("Initializing camera 2 - bzz bzz brrr")


# Nested Spans
@tracer.start_as_current_span("initialize-stage")
def initialize_stage():
    logging.info("Initializing stage")
    with tracer.start_as_current_span("align-axis"):
        logging.info("Aligning axis")


# Span attributes
def wake_up_mouse(mouse_id):
    with tracer.start_as_current_span("wake-up-mouse", attributes={"mouse.id": mouse_id}):
        logging.info("Good morning mousey %s", mouse_id)


################################################################################
#
#   Semantic Conventions
#
################################################################################


# Semantic Conventions from OTEL
@tracer.start_as_current_span("server-span")
def get_server() -> dict:
    address, port = "127.0.0.1", 8008
    trace.get_current_span().set_attribute(server_attributes.SERVER_ADDRESS, address)
    trace.get_current_span().set_attribute(server_attributes.SERVER_PORT, port)
    return {"address": address, "port": port}


################################################################################
#
#   Event
#
################################################################################


# Using Events within a Span
@tracer.start_as_current_span("connect-to-database")
def connect_to_database_server(server):
    logging.info(f"Connecting to {server['address']}:{server['port']}")
    trace.get_current_span().add_event("authenticating")
    trace.get_current_span().add_event("request sent")
    trace.get_current_span().add_event("connection established")
    logging.info("Connection established")


################################################################################
#
#   Links
#
################################################################################


# Mock async curriculum software response
def curriculum_software():
    return SpanContext(
        trace_id=0x4BF92F3577B34DA6A3CE929D0E0E4736,  # 32 hex characters
        span_id=0x00F067AA0BA902B7,  # 16 hex characters
        is_remote=True,
        trace_flags=TraceFlags(TraceFlags.SAMPLED),
    )


# Starting a session with a linked span from the curriculum software response
def start_session():
    logging.info("Grabbing curriculum from curriculum software")
    curriculum = curriculum_software()
    with tracer.start_as_current_span("link-1", links=[trace.Link(curriculum)]):
        logging.info("Starting new session")
        run_session()


################################################################################
#
#   Span Status / Exceptions
#
################################################################################


# Running a session with user interactions and handling span status/exceptions
def run_session():
    while True:
        interaction = input("Give input for mice (feed, hard-task, easy-task, finish):")
        if interaction == "finish":
            logging.info("Finishing session")
            break

        if interaction == "feed":
            with tracer.start_as_current_span("feeding"):
                logging.info("Feeding mice")
        elif interaction == "hard-task":
            with tracer.start_as_current_span("hard-task"):
                try:
                    logging.info("Performing hard task")
                    raise Exception("Hard task failed")
                except Exception as e:
                    logging.error("Hard task failed: %s", str(e))
                    trace.get_current_span().set_status(trace.Status(StatusCode.ERROR, str(e)))
        elif interaction == "easy-task":
            with tracer.start_as_current_span("easy-task"):
                logging.info("Performing easy task")


################################################################################
#
#   Main Execution
#
################################################################################


def main():
    initialize_camera_1()
    initialize_camera_2()
    initialize_stage()
    wake_up_mouse(614173)
    connect_to_database_server(get_server())
    start_session()


if __name__ == "__main__":
    main()
