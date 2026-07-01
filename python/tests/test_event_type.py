import json

from log_schema.models import EventType


def test_event_type_canonical_values():
    assert [e.value for e in EventType] == [
        "stage_start",
        "stage_complete",
        "stage_failure",
    ]


def test_event_type_serializes_to_string():
    # str-enum -> JSON value is the bare string, suitable for log extra=
    assert json.dumps(EventType.STAGE_START) == '"stage_start"'
