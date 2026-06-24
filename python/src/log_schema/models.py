from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class EventType(str, Enum):
    """Canonical event_type values (AIND logging standard).

    Per-event field: pass via the log call's extra, e.g.
    logging.info("starting", extra={"event_type": EventType.STAGE_START}).
    """

    STAGE_START = "stage_start"
    STAGE_COMPLETE = "stage_complete"
    STAGE_FAILURE = "stage_failure"


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

    acquisition_name: str  # required
    hostname: Optional[str] = None
    software_name: Optional[str] = None
    software_version: Optional[str] = None
    rig_id: Optional[str] = None
    instrument_id: Optional[str] = None
    subject_id: Optional[str] = None
    specimen_id: Optional[str] = None
    pipeline_name: Optional[str] = None
    process_name: Optional[str] = None
    user_id: Optional[str] = None

    model_config = {
        "extra": "allow",
    }
