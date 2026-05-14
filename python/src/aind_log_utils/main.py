from __future__ import annotations

import importlib.resources as resources
import logging
import logging.config
from datetime import datetime, timezone
from logging import LogRecord

import yaml
from pydantic import BaseModel
from pythonjsonlogger import json as log_json


def _model_to_fields(model: BaseModel | dict) -> dict:
    if isinstance(model, dict):
        return model
    elif isinstance(model, BaseModel):
        return model.model_dump(exclude_none=True)
    raise TypeError("Model must be a dict or pydantic BaseModel")


def _get_default_config():
    path = resources.files("aind_log_utils").joinpath("defaults/default-logging-config.yml")
    with open(path, "r") as f:
        config = yaml.safe_load(f.read())
    return config


class DefaultFormatter(log_json.JsonFormatter):
    def __init__(self, *args, model: dict | BaseModel | None = None, **kwargs):
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
        if "static_fields" not in kwargs and model:
            kwargs["static_fields"] = _model_to_fields(model)
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


def setup_logging(
    path_to_config: str | None = None,
    config: dict | None = None,
    model: BaseModel | dict | None = None,
):
    if path_to_config:
        try:
            with open(path_to_config, "r") as f:
                config = yaml.safe_load(f.read())
        except FileNotFoundError:
            print("config not found, using defaults")
        except yaml.YAMLError:
            print("config is invalid, using defaults")

    if config is None:
        config = _get_default_config()

    if model:
        new_fields = _model_to_fields(model)
        for formatter in config.get("formatters", {}).values():
            if formatter.get("()") == "aind_log_utils.main.DefaultFormatter":
                formatter.setdefault("static_fields", {}).update(new_fields)

    # Setup logger with configuration file
    logging.config.dictConfig(config)
