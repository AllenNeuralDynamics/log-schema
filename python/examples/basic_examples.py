import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from log_schema import DefaultFormatter, setup_logging

CONFIG_PATH = Path(__file__).resolve().parent / "configs" / "config.yml"
CONFIG_DICT: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "log_schema.DefaultFormatter",
            "static_fields": {"configure_by": "dictionary"},
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

################################################################################
#
#   Basic Setup Example
#
################################################################################


def setup_default():
    setup_logging()
    logging.info("Basic example of logging with log_schema!")


################################################################################
#
#   Custom Logging Configs Example
#
################################################################################


def setup_with_custom_config_file():
    """
    This example shows using a custom logging config (from logging.config) to setup logging. The
    config contents are loaded from a yaml file (config.yml)

    In the config file, we specify using the DefaultFormatter to ensure logs are formatted correctly
    """
    setup_logging(path_to_config=CONFIG_PATH)

    # Contains additional field "configure_by" with value "file"
    logging.info("This logger was configured with a custom file called config.yml")


def setup_with_custom_config_dict():
    """
    This example shows using a custom logging config (from logging.config) to setup logging. The
    config contents are loaded from a dictionary (CONFIG_DICT)

    In the config dictionary, we specify using the DefaultFormatter to ensure logs are formatted
    correctly.
    """

    setup_logging(config=CONFIG_DICT)

    # Contains additional field "configure_by" with value "dictionary"
    logging.info("This logger was configured with a custom config dict")


def setup_with_provided_custom_config():
    """
    This example shows using a provided custom logging config from the defaults module to setup 
    logging.
    """
    from log_schema.defaults import get_default_config

    setup_logging(config=get_default_config())
    logging.info("This logger was configured with custom default config from defaults module")


################################################################################
#
#   Custom Dynamic Fields Example
#
################################################################################


def setup_with_custom_fields_from_dict():
    setup_logging(model={"custom_field": "from_dictionary"})

    logging.info("Field defined from dictionary")


def setup_with_custom_fields_from_basemodel():
    """
    This example shows adding logging labels through the use of a pydantic BaseModel. The fields
    defined in the BaseModel will be added as static fields to the log formatter.

    By default, it will ignore empty (None) fields in the BaseModel.
    """

    class CustomModel(BaseModel):
        custom_field: str = "from_basemodel"

    setup_logging(model=CustomModel())

    logging.info("Field defined from pydantic model")


def setup_with_custom_fields_from_provided_models():
    """
    This example shows adding logging labels using a provided model from the log_schema.defaults 
    module.
    """
    from log_schema.defaults import AINDLogFields

    setup_logging(
        model=AINDLogFields(
            acquisition_name="123456_2026-01-01_23-00-00",
            software_name="test_software",
            software_version="1.0.0",
        )
    )
    logging.info("Field defined from provided model")


def setup_with_custom_fields_from_extras():
    """
    This example uses a dictionary to add additional logging labels.
    """
    setup_logging()
    logging.info("Field defined from extras", extra={"custom_field": "from_extras"})


################################################################################
#
#   Additional Handler After Setup
#
################################################################################


def setup_with_additional_handler():
    setup_logging()

    # Add an additional handler after setup
    additional_handler = logging.StreamHandler()

    # Need to add DefaultFormatter to new handler to ensure logs are formatted correctly
    #   formatter also takes in model field to load fields dynamically
    additional_handler.formatter = DefaultFormatter(model={"app_name": "test_app"})
    logging.getLogger().addHandler(additional_handler)

    logging.info("Two stream logs, one default, one with additional handler")


def main():
    examples = {
        "Default setup": setup_default,
        "Custom config - file": setup_with_custom_config_file,
        "Custom config - dict": setup_with_custom_config_dict,
        "Custom config - provided config": setup_with_provided_custom_config,
        "Custom fields - dict": setup_with_custom_fields_from_dict,
        "Custom fields - pydantic": setup_with_custom_fields_from_basemodel,
        "Custom fields - provided model": setup_with_custom_fields_from_provided_models,
        "Custom extra fields": setup_with_custom_fields_from_extras,
        "Custom handler": setup_with_additional_handler,
    }

    for example_name, example_func in examples.items():
        print(f"\n{'=' * 20} {example_name} {'=' * 20}\n")
        example_func()


if __name__ == "__main__":
    main()
