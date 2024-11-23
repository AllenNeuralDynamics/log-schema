import logging
import os
from unittest import mock
from aind_log_utils import log


def test_prepare_metadata():
    with mock.patch("platform.node", return_value="test-node"), \
         mock.patch("os.getpid", return_value=1234), \
         mock.patch.dict(os.environ, {
             "HOSTNAME": "test-host",
             "CO_COMPUTATION_ID": "test-comp-id",
             "CO_CAPSULE_ID": "test-version"
         }):
        metadata = log.prepare_metadata(
            process_name="test-process",
            mouse_id="mouse123",
            session_name="session-abc"
        )

    assert metadata["process_name"] == "test-process"
    assert metadata["mouse_id"] == "mouse123"
    assert metadata["session_name"] == "session-abc"
    assert metadata["hostname"] == "test-host"
    assert metadata["comp_id"] == "test-comp-id"
    assert metadata["version"] == "test-version"
    assert metadata["log_session"] != ""


def test_make_record_factory():
    metadata = {
        "hostname": "test-host",
        "comp_id": "test-comp-id",
        "version": "test-version",
        "log_session": "test-session",
        "user_name": "test-user",
        "mouse_id": "mouse123",
        "session_name": "session-abc",
        "process_name": "test-process",
    }

    factory = log.make_record_factory(metadata)
    record = factory(name="test",
                     level=logging.INFO,
                     pathname="path",
                     lineno=10,
                     msg="test-message",
                     args=(),
                     exc_info=None
                     )

    assert record.hostname == "test-host"
    assert record.comp_id == "test-comp-id"
    assert record.version == "test-version"
    assert record.log_session == "test-session"
    assert record.mouse_id == "mouse123"
    assert record.session_name == "session-abc"
    assert record.process_name == "test-process"


def test_logger_with_fixture(capsys):
    # Perform logging actions

    message_template = "Test"

    subject_id = "999999"
    session_name = f"{subject_id}-110824"

    log.setup_logging(
        "capsule",
        mouse_id=subject_id,
        session_name=session_name,
        send_start_log=False,
        )

    logging.info(message_template)

    captured = capsys.readouterr()
    expected_substrings = "999999, 999999-110824"
    assert expected_substrings in captured.out


def test_setup_logging_without_start_log(capsys):
    with mock.patch("aind_log_utils.log.resources.read_text", return_value="""
        version: 1
        formatters:
          default:
            format: '%(levelname)s:%(message)s'
        handlers:
          console:
            class: logging.StreamHandler
            formatter: default
            stream: ext://sys.stdout
        root:
          level: INFO
          handlers: [console]
    """):
        log.setup_logging(
            process_name="test-process",
            mouse_id="mouse123",
            session_name="session-abc",
            send_start_log=False
        )

        logging.info("Log message without start log")

    captured = capsys.readouterr()
    assert "INFO:Log message without start log" in captured.out
