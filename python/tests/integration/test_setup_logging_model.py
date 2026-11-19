import json
import logging

import pytest
from pydantic_core import PydanticSerializationError

from log_schema import DefaultFormatter, setup_logging
from tests.helpers.assertions import extract_log_entry, has_iso_timestamp
from tests.helpers.configs import ConfigBuilder
from tests.helpers.models import LogConfigModel


class SubclassedFormatter(DefaultFormatter):
    pass


@pytest.mark.parametrize(
    "model",
    [
        pytest.param(LogConfigModel(), id="pydantic model"),
        pytest.param({"app_name": "my_app", "env": "production"}, id="dict model"),
    ],
)
def test_setup_logging_pydantic_model(capsys, model):
    """
    Tests setup logging with a pydantic model or dict as the model parameter.
    Expect: Log message includes static fields from the model.
    """
    setup_logging(model=model)
    logging.info("Test log message")

    log_entry = extract_log_entry(capsys)

    assert has_iso_timestamp(log_entry)
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test log message"

    # Static fields from config
    assert log_entry["app_name"] == "my_app"
    assert log_entry["env"] == "production"


@pytest.mark.parametrize(
    "invalid_model",
    [
        pytest.param(12, id="invalid - int"),
        pytest.param("test", id="invalid - string"),
        pytest.param(["hello"], id="invalid - collection"),
    ],
)
def test_setup_logging_invalid_model_return_type_error(invalid_model):
    """
    Tests setup logging with an invalid model type, expecting a TypeError.
    Expect: TypeError is raised when the model type is invalid.
    """
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
    """
    Tests setup logging with a falsy model value, expecting it to be ignored.
    Expect: Falsy model values are ignored and do not add static fields to the log entry.
    """
    setup_logging(model=falsy_model)
    logging.info("Test log message")

    log_entry = extract_log_entry(capsys)
    assert "app_name" not in log_entry


def test_setup_logging_dict_model_values_converted_to_json_types(capsys):
    """
    Tests setup logging with a dict model containing values that need to be converted to JSON types.
    Expect: Values are converted to JSON-compatible types in the log entry.
    """
    setup_logging(model={"test": set([1, 2])})
    logging.info("Test log message")

    log_entry = extract_log_entry(capsys)

    assert sorted(log_entry["test"]) == [1, 2]


def test_setup_logging_dict_model_unserializable_value_raises():
    """
    Tests setup logging with a dict model containing an unserializable value
    Expect: PydanticSerializationError is raised when the model contains unserializable values.
    """
    with pytest.raises(PydanticSerializationError):
        setup_logging(model={"test": object()})


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param("log_schema.DefaultFormatter", id="package path"),
        pytest.param(f"{__name__}.SubclassedFormatter", id="subclass path"),
        pytest.param(SubclassedFormatter, id="class object"),
    ],
)
def test_setup_logging_adds_model_fields_to_json_output(capsys, factory):
    """
    Tests setup logging with different formatter factories.
    Expect: Model fields are added to the JSON output correctly.
        Only if formatter supports it (i.e. subclass from DefaultFormatter or compatible).
    """
    config = ConfigBuilder().get_config_dict(None, False)
    config["formatters"]["default"]["()"] = factory

    setup_logging(config=config, model={"app_name": "my_app"})
    logging.info("hello")

    assert json.loads(capsys.readouterr().out.strip())["app_name"] == "my_app"
