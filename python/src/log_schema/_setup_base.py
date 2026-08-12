from __future__ import annotations

import importlib.resources as resources
import logging
import logging.config
from datetime import datetime, timezone
from logging import LogRecord
from typing import Any

import yaml
from opentelemetry import trace
from pydantic import BaseModel
from pythonjsonlogger import json as log_json

# OTel uses INVALID_SPAN (all-zero IDs) when no span is active; skip those.
_INVALID_TRACE_ID = 0
_INVALID_SPAN_ID = 0


def _model_to_fields(model: BaseModel | dict) -> dict:
    if isinstance(model, dict):
        return model
    elif isinstance(model, BaseModel):
        return model.model_dump(exclude_none=True)
    raise TypeError("Model must be a dict or pydantic BaseModel")


def _get_default_config():
    path = resources.files("log_schema").joinpath("defaults/default-logging-config.yml")
    with open(path, "r") as f:
        config = yaml.safe_load(f.read())
    return config


class DefaultFormatter(log_json.JsonFormatter):
    def __init__(
        self,
        *args,
        model: dict | BaseModel | None = None,
        include_trace_context: bool = True,
        **kwargs,
    ):
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
        self.include_trace_context = include_trace_context

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        if not self.include_trace_context:
            return
        span_context = trace.get_current_span().get_span_context()
        if span_context.trace_id == _INVALID_TRACE_ID:
            return

        # TODO: remove this, i think otel auto injects trace_id and span_id into log records now, so this is redundant
        # # Format as hex per OpenTelemetry log data model.
        # log_record.setdefault("trace_id", format(span_context.trace_id, "032x"))
        # if span_context.span_id != _INVALID_SPAN_ID:
        #     log_record.setdefault("span_id", format(span_context.span_id, "016x"))

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
            if formatter.get("()") == "log_schema.main.DefaultFormatter":
                formatter.setdefault("static_fields", {}).update(new_fields)

    # Setup logger with configuration file
    logging.config.dictConfig(config)



