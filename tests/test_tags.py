from aind_log_utils import log
import logging

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
    print(captured.out)
    expected_substrings = "999999, 999999-110824"
    assert expected_substrings in captured.out
