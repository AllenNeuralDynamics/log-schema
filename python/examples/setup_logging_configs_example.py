import logging
from pathlib import Path
from typing import Any

from log_schema import setup_logging

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
#   Examples
#
################################################################################


# Setup logging from config file
def setup_with_custom_config_file():
    """
    This example shows using a custom logging config (from logging.config) to setup logging. The
    config contents are loaded from a yaml file (config.yml)

    In the config file, we specify using the DefaultFormatter to ensure logs are formatted correctly
    """
    setup_logging(path_to_config=CONFIG_PATH)

    # Contains additional field "configure_by" with value "file"
    logging.info("This logger was configured with a custom file called config.yml")


# Setup logging from config dictionary
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


# Setup logging from provided custom config
def setup_with_provided_custom_config():
    """
    This example shows using a provided custom logging config from the defaults module to setup 
    logging.
    """
    from log_schema.defaults import get_default_config

    setup_logging(config=get_default_config())
    logging.info("This logger was configured with custom default config from defaults module")


def main():
    examples = {
        "Setup logging from config file": setup_with_custom_config_file,
        "Setup logging from config dict": setup_with_custom_config_dict,
        "Setup logging from provided custom config": setup_with_provided_custom_config,
    }

    for example_name, example_func in examples.items():
        print(f"\n{example_name} \n{'-' * len(example_name)}\n")
        example_func()


if __name__ == "__main__":
    main()
