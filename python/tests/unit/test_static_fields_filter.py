import logging

from log_schema import StaticFieldsFilter
from tests.helpers.models import LogConfigModel


def test_static_fields_filter_does_not_override_extra():
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello", (), None)
    record.env = "dev"

    assert StaticFieldsFilter({"env": "prod", "app_name": "my_app"}).filter(record) is True
    assert record.env == "dev"
    assert record.app_name == "my_app"


def test_static_fields_filter_accepts_pydantic_model():
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello", (), None)

    StaticFieldsFilter(LogConfigModel(app_name="my_app")).filter(record)

    assert record.app_name == "my_app"
