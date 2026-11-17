import json
import logging
import sys

import pytest

from log_schema import DefaultFormatter, StaticFieldsFilter, setup_logging
from tests.helpers.assertions import extract_log_entry, has_iso_timestamp
from tests.helpers.configs import ConfigBuilder

################################################################################
#
#   Static field precedence
#
################################################################################


def test_setup_logging_config_model_and_extra_fields_precedence(capsys):
    """
    Tests setup logging with overlapping fields defined in config, model, and extra.
    Expect: Precedence order is extra > model > config.
    """

    # Create config and model with overlapping fields
    config = ConfigBuilder().get_config_dict(True, False)
    config["formatters"]["default"]["static_fields"] = {
        "field1": "from-config",
        "field2": "from-config-will-be-overridden",
        "field3": "from-config-will-be-overridden",
    }
    model = {"field2": "from-model", "field3": "from-model-will-be-overridden"}

    setup_logging(
        config=config,
        model=model,
    )
    logging.info("Test log message", extra={"field3": "from-extra"})

    log_entry = extract_log_entry(capsys)

    assert has_iso_timestamp(log_entry)
    assert log_entry["level"] == "INFO"
    assert log_entry["message"] == "Test log message"

    # Precedence order: extra > model > config
    assert log_entry["field1"] == "from-config"
    assert log_entry["field2"] == "from-model"
    assert log_entry["field3"] == "from-extra"


################################################################################
#
#   New logger behavior
#
################################################################################


@pytest.mark.parametrize(
    "has_own_handler, propagate, expected_outputs",
    [
        # expected_outputs: one bool per emitted line (in handler order), True if app_name present
        pytest.param(False, True, [True], id="no handler, propagate"),
        pytest.param(True, True, [False, True], id="own handler, propagate"),
        pytest.param(True, False, [False], id="own handler, no propagate"),
        # INFO is dropped; only WARNING+ reaches logging.lastResort (stderr)
        pytest.param(False, False, [], id="no handler, no propagate"),
    ],
)
def test_setup_logging_static_fields_on_new_loggers(
    capsys, has_own_handler, propagate, expected_outputs
):
    """
    Tests how static fields from setup_logging reach loggers created afterwards.
    Expect:
    - no handler, propagate=True: inherits root handler, has setup_logging fields
    - has handler, propagate=True: own handler does not have fields, but propagated output does
    - has handler, propagate=False: only own handler output, does not have setup_logging fields
    - no handler, propagate=False: has nothing, inherit nothing, output is empty
    """
    setup_logging(model={"app_name": "my_app"})

    logger = logging.getLogger(f"tests.new_logger.{has_own_handler}.{propagate}")
    logger.propagate = propagate
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(DefaultFormatter())
    if has_own_handler:
        logger.addHandler(handler)

    try:
        logger.info("Test log message")
    finally:
        logger.removeHandler(handler)
        logger.propagate = True

    lines = capsys.readouterr().out.strip().splitlines()
    log_entries = [json.loads(line) for line in lines]

    assert ["app_name" in entry for entry in log_entries] == expected_outputs


################################################################################
#
#   Multiple handlers (with StaticFieldsFilter) behavior
#
################################################################################


def test_multiple_handlers_fields_accumulate_in_handler_order(capsys):
    """
    Tests root handlers [A, B, C] where A and B each have a StaticFieldsFilter.
    Expect: filters mutate the shared LogRecord, so each handler sees its own fields plus those
    of every filtered handler before it.
    """
    config = _config_with_handlers(
        filters={"a": {"only_a": 1}, "b": {"only_b": 2}},
        handlers={"A": ["a"], "B": ["b"], "C": []},
    )
    setup_logging(config=config)
    logging.info("Test log message")

    a, b, c = _read_log_entries(capsys)

    assert a["only_a"] == 1
    assert "only_b" not in a
    assert (b["only_a"], b["only_b"]) == (1, 2)
    assert (c["only_a"], c["only_b"]) == (1, 2)


@pytest.mark.parametrize(
    "handler_order, expected_value",
    [
        pytest.param(["A", "B"], "from-a", id="A first"),
        pytest.param(["B", "A"], "from-b", id="B first"),
    ],
)
def test_multiple_handlers_first_filter_wins_on_shared_key(capsys, handler_order, expected_value):
    """
    Tests two handlers whose filters set the same key.
    Expect: the first filter to run sets the key; later filters skip it, for every handler.
    """
    filter_for = {"A": ["a"], "B": ["b"]}
    config = _config_with_handlers(
        filters={"a": {"shared": "from-a"}, "b": {"shared": "from-b"}},
        handlers={name: filter_for[name] for name in handler_order},
    )
    setup_logging(config=config)
    logging.info("Test log message")

    log_entries = _read_log_entries(capsys)

    assert [entry["shared"] for entry in log_entries] == [expected_value, expected_value]


def test_multiple_handlers_extra_beats_all_filters(capsys):
    """
    Tests extra= with multiple filtered handlers.
    Expect: extra is set on the record at creation, so no filter overrides it on any handler.
    """
    config = _config_with_handlers(
        filters={"a": {"shared": "from-a"}, "b": {"shared": "from-b"}},
        handlers={"A": ["a"], "B": ["b"], "C": []},
    )
    setup_logging(config=config)
    logging.info("Test log message", extra={"shared": "from-extra"})

    log_entries = _read_log_entries(capsys)

    assert [entry["shared"] for entry in log_entries] == ["from-extra"] * 3


def test_multiple_handlers_skipped_handler_does_not_apply_filter(capsys):
    """
    Tests a record below handler A's level.
    Expect: A's filter never runs, so later handlers only get B's fields.
    """
    config = _config_with_handlers(
        filters={"a": {"only_a": 1}, "b": {"only_b": 2}},
        handlers={"A": ["a"], "B": ["b"], "C": []},
    )
    config["handlers"]["A"]["level"] = "WARNING"
    setup_logging(config=config)
    logging.info("Test log message")

    b, c = _read_log_entries(capsys)

    assert "only_a" not in b and "only_a" not in c
    assert b["only_b"] == c["only_b"] == 2


################################################################################
#
#   Utility functions for tests
#
################################################################################


def _config_with_handlers(filters: dict[str, dict], handlers: dict[str, list[str]]) -> dict:
    """Root logger config with JSON stdout handlers in the given order, each with its filters."""
    return {
        "version": 1,
        "formatters": {"json": {"()": "log_schema.DefaultFormatter"}},
        "filters": {
            name: {"()": StaticFieldsFilter, "fields": fields} for name, fields in filters.items()
        },
        "handlers": {
            name: {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": "ext://sys.stdout",
                "filters": handler_filters,
            }
            for name, handler_filters in handlers.items()
        },
        "loggers": {"": {"handlers": list(handlers), "level": "INFO"}},
    }


def _read_log_entries(capsys) -> list[dict]:
    return [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
