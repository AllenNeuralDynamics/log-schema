import importlib
import sys

import pytest

from log_schema.cloudwatch import CloudWatchLogModel, get_default_config


def test_get_default_config_includes_cloudwatch_handler():
    config = get_default_config()

    assert config["handlers"]["cloudwatch"]["class"] == "watchtower.CloudWatchLogHandler"
    assert "cloudwatch" in config["loggers"][""]["handlers"]


def test_get_default_config_returns_fresh_copy():
    get_default_config()["handlers"].clear()

    assert "cloudwatch" in get_default_config()["handlers"]


def test_cloudwatch_model_allows_extra_fields():
    model = CloudWatchLogModel(service="svc", team="platform")

    assert model.model_dump(exclude_none=True) == {"service": "svc", "team": "platform"}


def test_import_without_watchtower_raises_helpful_error(monkeypatch):
    monkeypatch.setitem(sys.modules, "watchtower", None)
    for name in [m for m in sys.modules if m.startswith("log_schema.cloudwatch")]:
        monkeypatch.delitem(sys.modules, name)

    with pytest.raises(ImportError, match=r"log-schema\[cloudwatch\]"):
        importlib.import_module("log_schema.cloudwatch")
