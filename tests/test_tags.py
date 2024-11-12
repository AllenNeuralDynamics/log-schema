from aind_log_utils import log


def test_logger_with_fixture(capsys):
    # Perform logging actions

    message_template = "Test"

    subject_id = "999999"
    session_id = f"{subject_id}-110824"

    logger = log.setup_logging(
        "codeocean-test",
        subject_id=subject_id,
        session_id=session_id,
        )

    logger.info(message_template)

    captured = capsys.readouterr()
    expected_substrings = "Test, subject_id=999999, session_id=999999-110824"
    assert expected_substrings in captured.out
    