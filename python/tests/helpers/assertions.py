import json

from dateutil import parser


def extract_log_entry(capsys):
    captured = capsys.readouterr()
    output = captured.out.strip()
    try:
        log_entry = json.loads(output)
    except json.JSONDecodeError:
        assert False, "Output is not valid JSON"
    return log_entry


def has_iso_timestamp(log_entry):
    try:
        parser.isoparse(log_entry["timestamp"])
    except ValueError:
        assert False, "Timestamp is not in ISO 8601 format"
    return True
