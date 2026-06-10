import logging

import pytest
from pydantic import ValidationError

from log_schema.main import setup_logging
from log_schema.models import LogFields


def test_log_fields_drops_none():
    fields = LogFields(
        acquisition_name="123456_2026-01-01_23-00-00",
        process_name="aind-pophys-converter",
    )

    assert fields.model_dump(exclude_none=True) == {
        "acquisition_name": "123456_2026-01-01_23-00-00",
        "process_name": "aind-pophys-converter",
    }


def test_log_fields_requires_acquisition_name():
    with pytest.raises(ValidationError):
        LogFields()


def test_log_fields_allows_extra():
    fields = LogFields(
        acquisition_name="123456_2026-01-01_23-00-00",
        custom_metric=42,
    )

    assert fields.model_dump(exclude_none=True)["custom_metric"] == 42


def test_log_fields_injected_on_every_line(capsys):
    setup_logging(
        model=LogFields(
            acquisition_name="123456_2026-01-01_23-00-00",
            process_name="aind-pophys-converter",
        )
    )
    logging.info("hello")

    output = capsys.readouterr().out.strip()
    assert '"acquisition_name": "123456_2026-01-01_23-00-00"' in output
    assert '"process_name": "aind-pophys-converter"' in output
