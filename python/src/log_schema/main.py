from __future__ import annotations

import copy
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
    path = resources.files("log_schema").joinpath("defaults/default-logging-config.yml")
    with open(path, "r") as f:
        config = yaml.safe_load(f.read())
    return config


def _get_default_cloudwatch_config():
    "Load the bundled default-plus-CloudWatch logging config."
    
    path = resources.files("log_schema").joinpath(
        "defaults/default-cloudwatch-logging-config.yml"
    )
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


def _apply_model(config: dict, model: BaseModel | dict) -> None:
    "Inject model fields as static_fields on every DefaultFormatter."
    new_fields = _model_to_fields(model)
    for formatter in config.get("formatters", {}).values():
        if formatter.get("()") == "log_schema.main.DefaultFormatter":
            formatter.setdefault("static_fields", {}).update(new_fields)


def _uses_cloudwatch(config) -> bool:
    "Return True if any handler in config is a CloudWatch/watchtower handler."
    if not isinstance(config, dict):
        return False
    for handler in config.get("handlers", {}).values():
        handler_class = str(handler.get("class", ""))
        if "watchtower" in handler_class or "CloudWatch" in handler_class:
            return True
    return False


def _without_cloudwatch(config: dict) -> dict:
    "Return a copy of config with CloudWatch/watchtower handlers removed."
    stripped = copy.deepcopy(config)
    cloudwatch_handlers = {
        name
        for name, handler in stripped.get("handlers", {}).items()
        if "watchtower" in str(handler.get("class", ""))
        or "CloudWatch" in str(handler.get("class", ""))
    }
    for name in cloudwatch_handlers:
        stripped["handlers"].pop(name, None)
    scopes = list(stripped.get("loggers", {}).values())
    if "root" in stripped:
        scopes.append(stripped["root"])
    for scope in scopes:
        if "handlers" in scope:
            scope["handlers"] = [
                h for h in scope["handlers"] if h not in cloudwatch_handlers
            ]
    return stripped


def setup_logging(
    path_to_config: str | None = None,
    config: dict | None = None,
    model: BaseModel | dict | None = None,
    use_cloudwatch: bool = False,
):
    """Configure the root logger from a file, dict, or bundled default.

    Parameters
    ----------
    path_to_config : str, optional
        Path to a YAML logging config. If it cannot be read, the bundled
        default is used instead.
    config : dict, optional
        A logging config dict, used when ``path_to_config`` is not given.
    model : BaseModel or dict, optional
        Static fields injected onto every ``DefaultFormatter`` (e.g. an
        acquisition/process name attached to every log record).
    use_cloudwatch : bool, default False
        When neither ``path_to_config`` nor ``config`` is supplied, select
        the bundled console+CloudWatch config instead of console-only, so
        consumers get CloudWatch logging without shipping their own YAML.
        If the CloudWatch handler cannot be initialized (e.g. no AWS
        credentials outside Code Ocean), logging degrades to console only
        rather than raising.
    """
    if path_to_config:
        try:
            with open(path_to_config, "r") as f:
                config = yaml.safe_load(f.read())
        except FileNotFoundError:
            print("config not found, using defaults")
        except yaml.YAMLError:
            print("config is invalid, using defaults")

    if config is None:
        config = (
            _get_default_cloudwatch_config()
            if use_cloudwatch
            else _get_default_config()
        )

    if model:
        _apply_model(config, model)

    # Setup logger with configuration file
    try:
        logging.config.dictConfig(config)
    except ValueError:
        # A handler failed to initialize. If it is a CloudWatch handler
        # (commonly missing AWS credentials outside Code Ocean), degrade to
        # console-only logging instead of crashing the program. Any other
        # invalid-config error is re-raised.
        if not _uses_cloudwatch(config):
            raise
        logging.config.dictConfig(_without_cloudwatch(config))
        logging.warning(
            "CloudWatch logging handler could not be initialized; "
            "falling back to console logging."
        )
