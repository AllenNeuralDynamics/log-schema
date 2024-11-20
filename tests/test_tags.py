import pytest
from aind_log_utils import log


@pytest.fixture
def log_record():
    class Record:
        def __init__(self):
            self.levelname = "INFO"
            self.lineno = 100
            self.module = "aind-log-utils"
            self.created = 1732048506.937127
            self.msecs = 0

        def getMessage(self):
            return "test log message"

    return Record()


def test_json_formatter(log_record):
    formatter = log.JsonFormatter()
    expected = ('{"level": "INFO", "date": "2024-11-19 12:35:06,000", "message": "test log message", "module": '
                '"aind-log-utils", "lineno": 100}')
    assert expected == formatter.format(log_record)


def test_logger_with_fixture(capsys):
    # Perform logging actions

    message_template = "Test"

    subject_id = "999999"
    session_name = f"{subject_id}-110824"

    logger = log.setup_logging(
        "capsule",
        mouse_id=subject_id,
        session_name=session_name,
    )

    logger.info(message_template)

    captured = capsys.readouterr()
    expected_substrings = "999999, 999999-110824"
    assert expected_substrings in captured.out
