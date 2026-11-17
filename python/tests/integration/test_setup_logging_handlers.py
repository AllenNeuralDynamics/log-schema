import logging

from log_schema import StaticFieldsFilter, setup_logging
from tests.helpers.configs import ConfigBuilder


def test_setup_logging_adds_model_fields_to_every_handler():
    """
    Tests that setup_logging adds model fields to every handler.
    Expect: Each handler has a StaticFieldsFilter added.
    """
    config = ConfigBuilder().get_config_dict(True, False)
    config["handlers"]["second"] = {"class": "logging.NullHandler"}
    config["loggers"][""]["handlers"].append("second")

    setup_logging(config=config, model={"app_name": "my_app"})

    for handler in logging.getLogger().handlers:
        assert any(isinstance(f, StaticFieldsFilter) for f in handler.filters)


def test_setup_logging_keeps_existing_handler_filters():
    """
    Tests that setup_logging keeps existing handler filters intact.
    Expect: Existing filters are preserved and StaticFieldsFilter is added alongside them.
    """
    config = ConfigBuilder().get_config_dict(True, False)
    config["filters"] = {"existing": {"name": "some.logger"}}
    config["handlers"]["console"]["filters"] = ["existing"]

    setup_logging(config=config, model={"app_name": "my_app"})

    (handler,) = logging.getLogger().handlers
    assert len(handler.filters) == 2
