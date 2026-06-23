import json
import logging
import logging.config
from pathlib import Path
from typing import Any, Optional

import yaml
from jinja2 import Template
from pythonjsonlogger.core import RESERVED_ATTRS, BaseJsonFormatter, merge_record_extra


class HumanFormatterWithExtras(logging.Formatter):
    """A formatter that includes extra fields in the log output."""

    def __init__(self, *args, static_fields: dict[str, Any] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.static_fields = static_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        # Merge extra fields into the record
        extras = {**self.static_fields}
        merge_record_extra(record, extras, RESERVED_ATTRS)
        # Save and restore msg/args so shared LogRecord isn't permanently mutated
        # (the same record object is passed to every handler)
        original_msg, original_args = record.msg, record.args
        record.msg = f"{record.getMessage()} | {json.dumps(extras)}"
        record.args = None
        result = super().format(record)
        record.msg, record.args = original_msg, original_args
        return result


def add_log_context(fields: dict, logger: Optional[logging.Logger] = None):
    """Add static fields to any BaseJsonFormatter instances on the logger (default to root logger)

    >>> logging.dictConfig(config) # load logging config from somewhere
    >>> add_log_context({'software_name': 'example', 'software_version': '1.0.0'})
    """
    if logger is None:
        logger = logging.getLogger()
    for handler in logger.handlers:
        formatter = handler.formatter
        if isinstance(formatter, (BaseJsonFormatter, HumanFormatterWithExtras)):
            formatter.static_fields.update(fields)


def configure_logging(config_path: Path, **kwargs):
    """Load a logging config from a YAML file and apply it to the root logger.

    >>> configure_logging(Path("logging_config.yml"), software_name="example", software_version="1.0.0")
    """

    # Read the YAML file as a string
    with open(config_path, "r") as f:
        template_string = f.read()

    # Compile the string into a Jinja Template object
    template = Template(template_string)

    # Render and inject data using keyword arguments
    rendered_output = template.render(**kwargs)

    # Load the rendered YAML into a Python dictionary
    config_dict = yaml.safe_load(rendered_output)

    # Apply the logging configuration
    logging.config.dictConfig(config_dict)
