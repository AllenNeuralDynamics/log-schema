import importlib.resources as resources
import logging
import logging.config
import yaml

from datetime import datetime, timezone
from logging import LogRecord
from pydantic import BaseModel
from pythonjsonlogger import jsonlogger as log_json


class DefaultFormatter(log_json.JsonFormatter):
    def __init__(self, *args, models: dict | BaseModel | None = None, **kwargs):
        if not args and "fmt" not in kwargs:
            kwargs["fmt"] = "{asctime}{levelname}{message}"
            kwargs["style"] = "{"
        if "reserved_attrs" not in kwargs:
            kwargs["reserved_attrs"] = [
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "message",
                "module",
                "msecs",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "taskName",
                "thread",
                "threadName",
                "color_message",
            ]
        if "rename_fields" not in kwargs:
            kwargs["rename_fields"] = {
                "asctime": "timestamp",
                "levelname": "level",
            }
        if "static_fields" not in kwargs and models:
            if isinstance(models, dict):
                kwargs["static_fields"] = models
            else:
                kwargs["static_fields"] = models.model_dump(exclude_none=True)
        super().__init__(*args, **kwargs)

    def formatTime(self, record: LogRecord, datefmt=None) -> str:
        """
        Format timestamp as ISO-8601 UTC
        Parameters
        ----------
        record : LogRecord
        datefmt : str, optional
          Default is None

        Returns
        -------
        str

        """
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _get_default_config():
    path = resources.files("aind_log_utils").joinpath("defaults/default-logging-config.yml")
    with open(path, "r") as f:
        config = yaml.safe_load(f.read())
    return config


def setup_logging(
    path_to_config: str | None = None,
    config: dict | None = None,
    model: BaseModel | dict | None = None,
):
    try:
        with open(path_to_config, "r") as f:
            config = yaml.safe_load(f.read())
    except Exception:
        if path_to_config:
            print("config not found using defaults")
        config = _get_default_config()

    # In the config, if formatter is using the DefaultFormatter, add static fields from the model to that formatter
    # Only adds from model if static fields is not already defined
    for formatter_key in config["formatters"]:
        formatter = config["formatters"][formatter_key]
        if "()" in formatter and formatter["()"] == "aind_log_utils.main.DefaultFormatter":
            if model:
                if "static_fields" not in formatter or formatter["static_fields"] is None:
                    formatter["static_fields"] = {}
                if isinstance(model, dict):
                    new_fields = model.items()
                else:
                    new_fields = model.model_dump(exclude_none=True).items()
                for field, value in new_fields:
                    formatter["static_fields"][field] = value

    # Setup logger with configuration file
    logging.config.dictConfig(config)
