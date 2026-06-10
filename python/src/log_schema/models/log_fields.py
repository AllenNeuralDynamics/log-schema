from __future__ import annotations

from pydantic import BaseModel


class LogFields(BaseModel):
    """Canonical contextual log fields (AIND logging standard).

    Pass to setup_logging(model=...) to inject as static fields on every log
    line. acquisition_name is required; other fields are optional and None
    values are dropped; extra fields are allowed. See the README "Fields/Labels"
    table for field meanings.

    Example
    -------
    >>> from log_schema.main import setup_logging
    >>> from log_schema.models import LogFields
    >>> setup_logging(model=LogFields(
    ...     acquisition_name="123456_2026-01-01_23-00-00",
    ...     process_name="aind-pophys-converter",
    ... ))
    """

    acquisition_name: str
    hostname: str | None = None
    software_name: str | None = None
    software_version: str | None = None
    rig_id: str | None = None
    instrument_id: str | None = None
    subject_id: str | None = None
    specimen_id: str | None = None
    pipeline_name: str | None = None
    process_name: str | None = None
    user_id: str | None = None

    model_config = {
        "extra": "allow",
    }
