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
    path = resources.files("log_schema").joinpath("default-logging-config.yml")
    with open(path, "r") as f:
        config = yaml.safe_load(f.read())
    return config


class DefaultFormatter(log_json.JsonFormatter):
    def __init__(self, *args, model: BaseModel | None = None, **kwargs):
        if not args and "fmt" not in kwargs:
            kwargs["fmt"] = "{asctime}{levelname}{message}"
        if not args and "style" not in kwargs:
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
        self.model = model
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

    @property
    def dynamic_fields(self) -> dict:
        return self.model.model_dump(exclude_none=True) if self.model else {}

    def format(self, record: LogRecord) -> str:
        for key, value in self.dynamic_fields.items():
            if (
                key not in dir(record)
                and key not in key not in self.static_fields
                and key not in self.reserved_attrs
            ):
                setattr(record, key, value)
        return super().format(record)


def setup_logging(
    path_to_config: str | None = None,
    config: dict | None = None,
    model: BaseModel | None = None,
    static_fields: dict | None = None,
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

    # TODO: test with static_fields from a model_dump
    # (how does it handle nested objects and custom types)
    if static_fields:
        for formatter in config.get("formatters", {}).values():
            if formatter.get("()") == "log_schema.main.DefaultFormatter":
                formatter.setdefault("static_fields", {}).update(static_fields)

    # Setup logger with configuration file
    logging.config.dictConfig(config)

    # Add model to handlers with DefaultFormatter
    # DefaultFormatter has logic to dynamically generate fields from the model object
    if model:
        for handler in logging.getLogger().handlers:
            if handler and isinstance(handler.formatter, DefaultFormatter):
                handler.formatter.model = model
