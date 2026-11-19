import logging
from pathlib import Path

from log_schema import setup_logging

CONFIG_PATH = Path(__file__).resolve().parent / "configs" / "config_console_formatter.yml"


# Setup logging using console formatter
def setup_logging_with_custom_console_formatter():
    """
    Setup logging using a custom console formatter defined in the config file.
    The format template is specified in the configuration.

    Like DefaultFormatter we can also define template in a configuration dict or
    directly by creating a ConsoleFormatter instance.
    """
    setup_logging(path_to_config=CONFIG_PATH)

    logging.info("Log formatted with custom console formatter")


if __name__ == "__main__":
    setup_logging_with_custom_console_formatter()
