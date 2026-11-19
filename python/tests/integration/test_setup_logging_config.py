import json
import logging
from unittest.mock import mock_open, patch

import pytest
from dateutil import parser

from log_schema import setup_logging
from tests.helpers.assertions import extract_log_entry, has_iso_timestamp
from tests.helpers.configs import ConfigBuilder


def test_setup_logging_defaults(capsys):
    """
    Tests basic setup of logging (no custom options)
    Expect: Log message is formatted with default settings.
    """
    setup_logging()
    logging.info("Test log message")

    log_entry = extract_log_entry(capsys)

    assert has_iso_timestamp(log_entry)
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test log message"


@pytest.mark.parametrize(
    "mock_path_content, config, expected_field",
    [
        pytest.param(
            None,
            ConfigBuilder().get_config_dict("default", True),
            "app_name",
            id="config dict",
        ),
        pytest.param(
            ConfigBuilder().get_config_file_content(),
            None,
            "i-am-from-yaml",
            id="config yaml",
        ),
        pytest.param(
            ConfigBuilder().get_config_file_content(),
            ConfigBuilder().get_config_dict("default", True),
            "i-am-from-yaml",
            id="config dict + yaml",
        ),
    ],
)
def test_setup_logging_loading(capsys, mock_path_content, config, expected_field):
    """
    Tests loading config from file path and config dict.
    Expect: If both file and dict are provided, config file should take precedence.
    """
    if mock_path_content:
        with patch("builtins.open", mock_open(read_data=mock_path_content)):
            setup_logging(path_to_config="fake_path.yml", config=config)
    else:
        setup_logging(path_to_config=None, config=config)

    logging.info("Test log message")

    log_entry = extract_log_entry(capsys)

    assert expected_field in log_entry
    if expected_field == "app_name":
        assert "i-am-from-yaml" not in log_entry
    else:
        assert "app_name" not in log_entry


def test_setup_logging_custom_config_no_default_formatter(capsys):
    """
    Tests setup logging with a custom config that has no default formatter.
    Expect: Log message plain formatting
    """
    setup_logging(config=ConfigBuilder().get_config_dict(None, False))
    logging.info("Test log message")

    output = capsys.readouterr().out.strip()

    # Using user-defined config with no formatter
    assert output == "Test log message"


def test_setup_logging_custom_config_with_default_formatter_with_static_fields(capsys):
    """
    Tests setup logging with a custom config that has a default formatter and static fields.
    Expect: Log message is formatted with default formatter and includes static fields.
    """
    setup_logging(config=ConfigBuilder().get_config_dict("default", True))
    logging.info("Test log message")

    log_entry = extract_log_entry(capsys)

    assert has_iso_timestamp(log_entry)
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test log message"

    # Static fields from config
    assert log_entry["app_name"] == "my_app"
    assert log_entry["env"] == "production"


def test_setup_logging_custom_config_with_console_formatter_template(capsys):
    """
    Tests setup logging with a custom config that uses the console formatter and a template.
    Expect: The template reaches the formatter, model fields are injected, and output is not JSON.
    """
    config = ConfigBuilder().get_config_dict("console", False)
    config["formatters"]["default"]["template"] = "%(level)s | %(app_name)s | %(message)s"

    setup_logging(config=config, model={"app_name": "my_app"})
    logging.info("Test log message")

    assert capsys.readouterr().out.strip() == "INFO | my_app | Test log message"


def test_invalid_config_path_uses_default(capsys):
    """
    Tests setup logging with an invalid config path.
    Expect: Default config is used and a warning message is printed.
    """
    setup_logging(path_to_config="non_existent_config.yml")

    logging.info("Test log message")

    captured = capsys.readouterr()
    output = captured.out.strip().split("\n")

    assert output[0] == "config not found, using defaults"

    # Test that output is valid json
    try:
        log_entry = json.loads(output[1])
    except json.JSONDecodeError:
        assert False, "Output is not valid JSON"

    # Test that timestamp is in ISO 8601 format
    try:
        parser.isoparse(log_entry["timestamp"])
    except ValueError:
        assert False, "Timestamp is not in ISO 8601 format"

    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test log message"


def test_setup_logging_invalid_dictConfig_raises_error():
    """
    Tests setup logging with an invalid dictConfig.
    Expect: ValueError is raised when the config is invalid.
    """
    with patch(
        "builtins.open", mock_open(read_data=ConfigBuilder().get_invalid_config_file_content())
    ):
        with pytest.raises(ValueError):
            setup_logging(path_to_config="fake_path.yml")


def test_setup_logging_does_not_mutate_caller_config():
    """
    Tests that setup_logging does not mutate the caller's config dictionary.
    Expect: The original config remains unchanged after setup_logging is called.
    """
    config = ConfigBuilder().get_config_dict("default", False)

    setup_logging(config=config, model={"app_name": "my_app"})

    assert config == ConfigBuilder().get_config_dict("default", False)
