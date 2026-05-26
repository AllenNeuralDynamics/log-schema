import logging
from typing import Any

from log_schema import setup_logging

CONFIG_DICT: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s\n%(name)s\n%(levelname)s\n%(funcName)s (%(filename)s:%(lineno)d)\
            \n%(message)s\n%(project)s\n%(version)s",
            "()": "log_schema.main.DefaultFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
            "stream": "ext://sys.stdout",
        },
        "web_handler": {
            "class": "logging.handlers.SocketHandler",
            "host": "eng-logtools.corp.alleninstitute.org",
            "level": "INFO",
            "port": 9000,
        },
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "web_handler"],
            "level": "INFO",
            "propagate": True,
        },
    },
}


def additional_setup_with_record_factory():
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.project = "fake-app"
        record.version = "1.0.0"
        return record

    logging.setLogRecordFactory(record_factory)

    logging.info("Test message - with record factory")


def additional_setup_with_extras():
    logging.info("Test message - with extras", extra={"project": "fake-app", "version": "1.0.0"})


def additional_setup_with_adapter():
    logger = logging.getLogger(__name__)
    adapter = logging.LoggerAdapter(logger, {"project": "fake-app", "version": "1.0.0"})
    adapter.info("Test message - with adapter")


def main():
    """
    Normally, fields would be added either through the config file ('static_fields' in formatter),
    or through using setup_logging with a model parameter (see basic_examples.py for examples).

    This does not work for the SIPE log server because fields are set with the formatter when using
    setup_logging.

    The SIPE log server expects a Socket (TCP) connection from the logging.handlers.SocketHandler,
    which sends a pickled LogRecord object (does not send formatter). This means that for the SIPE
    log server to get necessary fields, it needs to be set at the record level (either through
    extras, adapter, or record factory).

    Logs will still successfully be sent to the SIPE log server, but it will be missing two fields:

        - project (default to "log_server")
        - version (default to "unknown")

    Q) why not have setup_logging set fields in the record factory level?

        I wanted it to be in the formatter level because it is more explicit and less likely to
        cause unintended consequences. Setting it in the record level means other loggers would be
        affected (all your logs will contain the fields).

        I wanted to support having multiple loggers with various fields. This is especially
        important when importing a library that uses logging. I don't want to override a project
        with the logging inside a library.

    Q) why not have the SIPE log server use a different handler that supports formatters?

        Grafana + Loki already supports having formatters. Should migrate to this workflow.

    """
    setup_logging(config=CONFIG_DICT)

    additional_setup_with_extras()
    additional_setup_with_adapter()
    additional_setup_with_record_factory()


if __name__ == "__main__":
    main()
