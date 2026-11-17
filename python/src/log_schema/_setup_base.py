from __future__ import annotations

import importlib.resources as resources
import logging
import logging.config
from datetime import datetime, timezone
from logging import LogRecord
from typing import Any

import yaml
from pydantic import BaseModel, TypeAdapter
from pythonjsonlogger import json as log_json

################################################################################
#
#   Utilities
#
################################################################################


_FIELDS_ADAPTER = TypeAdapter(dict)


def _model_to_fields(model: BaseModel | dict) -> dict:
    # mode="json": OTLP can't encode datetime/UUID/Path/Enum/Decimal and drops them.
    if isinstance(model, BaseModel):
        return model.model_dump(mode="json", exclude_none=True)
    if isinstance(model, dict):
        # mode="json": OTLP can't encode datetime/UUID/Path/Enum/Decimal and drops them.
        fields = _FIELDS_ADAPTER.dump_python(model, mode="json")
        return {k: v for k, v in fields.items() if v is not None}
    raise TypeError("Model must be a dict or pydantic BaseModel")


def _get_default_config():
    path = resources.files("log_schema").joinpath("defaults/default-logging-config.yml")
    with open(path, "r") as f:
        config = yaml.safe_load(f.read())
    return config


################################################################################
#
#   Logging Filters and Formatters
#
################################################################################


_STATIC_FIELDS_FILTER = "log_schema_static_fields"


class StaticFieldsFilter(logging.Filter):
    """
    Adds fixed fields to every LogRecord.
    This mean all logs (new and existing) will have these fixed fields added.
    """

    def __init__(self, fields: BaseModel | dict | None = None):
        super().__init__()
        self.fields = _model_to_fields(fields or {})

    def filter(self, record: LogRecord) -> bool:
        for key, value in self.fields.items():
            if not hasattr(record, key):
                setattr(record, key, value)
        return True


class DefaultFormatter(log_json.JsonFormatter):
    def __init__(
        self,
        *args,
        model: dict | BaseModel | None = None,
        include_trace_context: bool = False,
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
        log_data: dict[str, Any],
        record: LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_data, record, message_dict)

        if not self.include_trace_context:
            return

        try:
            from opentelemetry import trace
        except ImportError as e:
            raise ImportError(
                "include_trace_context was turned on, but opentelemetry is not installed. "
                "To integrate traces/spans install opentelemetry and use setup_logging_otel()"
            ) from e

        context = trace.get_current_span().get_span_context()
        if context.is_valid:
            log_data["trace_id"] = f"{context.trace_id:032x}"
            log_data["span_id"] = f"{context.span_id:016x}"

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


################################################################################
#
#   Main Helper Function
#
################################################################################


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

    # dictConfig defaults to True, which silences loggers created before setup (e.g. at import).
    if isinstance(config, dict):
        config = {"disable_existing_loggers": False, **config}

    if model:
        fields = _model_to_fields(model)

        # Copy instead of mutating so the caller's config can be reused.
        config = {
            **config,
            # Add static fields filter to the configuration
            "filters": {
                **config.get("filters", {}),
                _STATIC_FIELDS_FILTER: {"()": StaticFieldsFilter, "fields": fields},
            },
            # Add filter to all handlers
            "handlers": {
                name: {**handler, "filters": [*handler.get("filters", []), _STATIC_FIELDS_FILTER]}
                for name, handler in config.get("handlers", {}).items()
            },
        }

    logging.config.dictConfig(config)
