import json
import logging
from datetime import datetime
from unittest.mock import mock_open, patch

import pytest

from aind_log_utils.main import setup_logging
from tests.logging_config_builders import ConfigBuilder
from tests.logging_model_builders import LogConfigModel


def test_setup_logging_defaults(capsys):
    setup_logging()
    logging.info("Test log message")

    log_entry = _extract_log_entry_from_capsys(capsys)

    assert _test_timestamp_format(log_entry)
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test log message"


@pytest.mark.parametrize(
    "mock_path_content, config, expected_field",
    [
        pytest.param(
            None,
            ConfigBuilder().get_config_dict(True, True),
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
            ConfigBuilder().get_config_dict(True, True),
            "i-am-from-yaml",
            id="config dict + yaml",
        ),
    ],
)
def test_setup_logging_loading(capsys, mock_path_content, config, expected_field):
    """Tests loading config from file path. If both file and dict are provided, config file
    should take precedence."""
    if mock_path_content:
        with patch("builtins.open", mock_open(read_data=mock_path_content)):
            setup_logging(path_to_config="fake_path.yml", config=config)
    else:
        setup_logging(path_to_config=None, config=config)

    logging.info("Test log message")

    log_entry = _extract_log_entry_from_capsys(capsys)

    assert expected_field in log_entry
    if expected_field == "app_name":
        assert "i-am-from-yaml" not in log_entry
    else:
        assert "app_name" not in log_entry


def test_setup_logging_custom_config_no_default_formatter(capsys):
    setup_logging(config=ConfigBuilder().get_config_dict(False, False))
    logging.info("Test log message")

    output = capsys.readouterr().out.strip()

    # Using user-defined config with no formatter
    assert output == "Test log message"


def test_setup_logging_custom_config_with_default_formatter_no_static_fields(capsys):
    setup_logging(config=ConfigBuilder().get_config_dict(True, False))
    logging.info("Test log message")

    log_entry = _extract_log_entry_from_capsys(capsys)

    assert _test_timestamp_format(log_entry)
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test log message"


def test_setup_logging_custom_config_with_default_formatter_with_static_fields(capsys):
    setup_logging(config=ConfigBuilder().get_config_dict(True, True))
    logging.info("Test log message")

    log_entry = _extract_log_entry_from_capsys(capsys)

    assert _test_timestamp_format(log_entry)
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test log message"

    # Static fields from config
    assert log_entry["app_name"] == "my_app"
    assert log_entry["env"] == "production"


def test_setup_logging_static_fields_and_extras(capsys):
    setup_logging(config=ConfigBuilder().get_config_dict(True, True))
    logging.info("Test log message", extra={"env": "dev", "user": "jessy"})

    log_entry = _extract_log_entry_from_capsys(capsys)

    assert _test_timestamp_format(log_entry)
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test log message"

    # Static fields from config
    assert log_entry["app_name"] == "my_app"
    assert log_entry["env"] == "dev"  # Extra should override static field from config
    assert log_entry["user"] == "jessy"


@pytest.mark.parametrize(
    "model",
    [
        pytest.param(LogConfigModel(), id="pydantic model"),
        pytest.param({"app_name": "my_app", "env": "production"}, id="dict model"),
    ],
)
def test_setup_logging_pydantic_model(capsys, model):
    setup_logging(model=model)
    logging.info("Test log message")

    log_entry = _extract_log_entry_from_capsys(capsys)

    assert _test_timestamp_format(log_entry)
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test log message"

    # Static fields from config
    assert log_entry["app_name"] == "my_app"
    assert log_entry["env"] == "production"


def test_setup_logging_model_and_config(capsys):
    setup_logging(
        model=LogConfigModel(app_name="my_app", env="production"),
        config=ConfigBuilder().get_config_dict(True, False),
    )
    logging.info("Test log message")

    log_entry = _extract_log_entry_from_capsys(capsys)

    assert _test_timestamp_format(log_entry)
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test log message"

    assert log_entry["app_name"] == "my_app"
    assert log_entry["env"] == "production"


def test_setup_logging_model_and_config_overlapping_fields(capsys):
    setup_logging(
        config=ConfigBuilder().get_config_dict(True, True),
        model=LogConfigModel(env="model-override"),
    )
    logging.info("Test log message")

    log_entry = _extract_log_entry_from_capsys(capsys)

    assert _test_timestamp_format(log_entry)
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test log message"

    # Static fields from model should take precedence over config
    assert log_entry["app_name"] == "my_app"
    assert log_entry["env"] == "model-override"


@pytest.mark.parametrize(
    "invalid_model",
    [
        pytest.param(12, id="invalid - int"),
        pytest.param("test", id="invalid - string"),
        pytest.param(["hello"], id="invalid - collection"),
    ],
)
def test_setup_logging_invalid_model_return_type_error(invalid_model):
    with pytest.raises(TypeError):
        setup_logging(model=invalid_model)


@pytest.mark.parametrize(
    "falsy_model",
    [
        pytest.param([], id="invalid - empty list"),
        pytest.param("", id="invalid - empty string"),
    ],
)
def test_setup_logging_falsy_model_return_is_ignored(capsys, falsy_model):
    setup_logging(model=falsy_model)
    logging.info("Test log message")

    log_entry = _extract_log_entry_from_capsys(capsys)
    assert "app_name" not in log_entry


def test_setup_logging_invalid_data_model_return_str(capsys):
    setup_logging(model={"test": set([1, 2])})  # Invalid model value
    logging.info("Test log message")

    log_entry = _extract_log_entry_from_capsys(capsys)

    # python-json-logger converts un-serializable fields to strings
    assert log_entry["test"] == "{1, 2}"


def test_invalid_config_path_uses_default(capsys):
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
        datetime.fromisoformat(log_entry["timestamp"])
    except ValueError:
        assert False, "Timestamp is not in ISO 8601 format"

    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test log message"


def test_setup_logging_invalid_dictConfig_raises_error():
    """This error is thrown by the dictConfig function"""
    with patch(
        "builtins.open", mock_open(read_data=ConfigBuilder().get_invalid_config_file_content())
    ):
        with pytest.raises(ValueError):
            setup_logging(path_to_config="fake_path.yml")


################################################################################
#
#   Utility functions for tests
#
################################################################################


def _extract_log_entry_from_capsys(capsys):
    captured = capsys.readouterr()
    output = captured.out.strip()
    try:
        log_entry = json.loads(output)
    except json.JSONDecodeError:
        assert False, "Output is not valid JSON"
    return log_entry


def _test_timestamp_format(log_entry):
    try:
        datetime.fromisoformat(log_entry["timestamp"])
    except ValueError:
        assert False, "Timestamp is not in ISO 8601 format"
    return True
