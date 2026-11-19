import json
import logging
import sys

import pytest

from log_schema import DefaultFormatter, setup_logging
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
    config = ConfigBuilder().get_config_dict("default", False)
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
    Tests how fields from setup_logging reach loggers created afterwards.
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
