import logging
from pathlib import Path

from aind_log_utils import setup_logging, DefaultFormatter
from pydantic_settings import BaseSettings


CONFIG_PATH = Path(__file__).resolve().parent / "configs" / "aind.yml"


class AINDLogFields(BaseSettings):
    project_name: str = "aind-thingy-doo-dad"
    acquisition_name: str = "beep-boop-grabber"


class FakeInstrumentFields(BaseSettings):
    instrument_id: str = "1234"
    instrument_type: str = "microscope"


def setup_logging_basic():
    setup_logging(model=AINDLogFields())
    logging.info("Test - basic setup")

def setup_logging_basic_dict_as_model():
    setup_logging(model={"test": "boop"})
    logging.info("Test - basic setup")


def setup_logging_with_config():
    setup_logging(path_to_config=str(CONFIG_PATH))
    logging.info("Test - setup with config")


def setup_logging_with_config_additional_fields():
    setup_logging(path_to_config=str(CONFIG_PATH), model=FakeInstrumentFields())
    logging.info("Test - setup with config + additional fields from model")


def setup_logging_and_then_add_handler():
    setup_logging(model=AINDLogFields())

    import sys

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.formatter = DefaultFormatter(models=FakeInstrumentFields())

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    logging.info("TWO OF ME, TWINSIES")


def setup_logging_filter_example():
    import sys

    setup_logging(model=AINDLogFields())

    root_logger = logging.getLogger()
    root_logger.handlers[0].addFilter(logging.Filter("app"))

    # These loggers propagates logs to the root (which has our formatter & stream handler)
    logging.getLogger("app").info("This should show up")
    logging.getLogger("app.boop").info("This should show up")
    logging.getLogger("instrument").info("This shouldn't show up")

    # This is how you would setup a new logger with a different formatter/handler
    # No longer propagates, filter doesn't apply to it. 
    new_logger = logging.getLogger("instrument")
    new_handler = logging.StreamHandler(sys.stdout)
    new_handler.setFormatter(DefaultFormatter(models=FakeInstrumentFields()))
    new_logger.addHandler(new_handler)
    new_logger.propagate = False
    new_logger.info("different formatter")

    # Re-add filter to this handler in this new_logger
    new_logger.addFilter(logging.Filter("app"))
    new_logger.info("re-add our filter, but now this won't show up")


def main():
    examples = {
        "Basic Example": setup_logging_basic,
        "Basic Example with Dict as Model": setup_logging_basic_dict_as_model,
        "Setup with Config": setup_logging_with_config,
        "Setup with Config + Additional Fields": setup_logging_with_config_additional_fields,
        "Setup logging and then add handler": setup_logging_and_then_add_handler,
        "Filter example": setup_logging_filter_example,
    }

    for example_name, example_func in examples.items():
        print(f"\n{'=' * 20} {example_name} {'=' * 20}\n")
        example_func()


if __name__ == "__main__":
    main()
