from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    """Canonical event_type values (AIND logging standard).

    Per-event field: pass via the log call's extra, e.g.
    logging.info("starting", extra={"event_type": EventType.STAGE_START}).
    """

    STAGE_START = "stage_start"
    STAGE_COMPLETE = "stage_complete"
    STAGE_FAILURE = "stage_failure"
