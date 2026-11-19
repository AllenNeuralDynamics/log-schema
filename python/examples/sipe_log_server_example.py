import logging

from opentelemetry import trace

from log_schema import setup_logging, setup_logging_otel
from log_schema.sipe import SIPELogFields, get_default_config


def basic_example():
    setup_logging(
        config=get_default_config(),
        model=SIPELogFields(software_name="log_schema_test", software_version="1.0.0"),
    )
    logging.info("Test log - basic example")


def otel_example():
    additional_fields = {"user": "jessy", "role": "developer", "cool": True}
    setup_logging_otel(
        config=get_default_config(),
        resource=SIPELogFields(software_name="log_schema_test", software_version="1.0.0"),
        model=additional_fields,
        console_exporter=True,
    )
    logging.info("Test log - otel example")

    tracer = trace.get_tracer("Log Schema - OTEL Example")

    @tracer.start_as_current_span("traced_function")
    def traced_function():
        logging.info("Inside traced function")

    traced_function()
    logging.info("Finished otel example")


def main():
    # basic_example()
    otel_example()


if __name__ == "__main__":
    main()
