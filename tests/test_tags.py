""" Tests for the log utility functions """
import logging
import os
from unittest import mock, TestCase
from aind_log_utils import log


class TestLogUtils(TestCase):
    """
    Test the log utility functions
    """
    def test_prepare_metadata(self):
        """
        Test that the metadata is correctly prepared
        """
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

        self.assertEqual(metadata["process_name"], "test-process")
        self.assertEqual(metadata["mouse_id"], "mouse123")
        self.assertEqual(metadata["session_name"], "session-abc")
        self.assertEqual(metadata["hostname"], "test-host")
        self.assertEqual(metadata["comp_id"], "test-comp-id")
        self.assertEqual(metadata["version"], "test-version")
        self.assertNotEqual(metadata["log_session"], "")

    def test_make_record_factory(self):
        """
        Test that the record factory is correctly created
        """
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

        self.assertEqual(record.hostname, "test-host")
        self.assertEqual(record.comp_id, "test-comp-id")
        self.assertEqual(record.version, "test-version")
        self.assertEqual(record.log_session, "test-session")
        self.assertEqual(record.mouse_id, "mouse123")
        self.assertEqual(record.session_name, "session-abc")
        self.assertEqual(record.process_name, "test-process")

    def test_logger_with_fixture(self):
        """
        Test that the logger is correctly set up
        """
        # Simulate capturing logs with capsys equivalent
        from io import StringIO
        import sys

        captured_output = StringIO()
        sys.stdout = captured_output

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

        # Restore sys.stdout
        sys.stdout = sys.__stdout__

        # Check captured output
        captured_content = captured_output.getvalue()
        expected_substrings = "999999, 999999-110824"
        self.assertIn(expected_substrings, captured_content)

    def test_setup_logging_without_start_log(self):
        """
        Test that the logger is correctly set up without sending the start log
        """
        # Simulate capturing logs with capsys equivalent
        from io import StringIO
        import sys

        captured_output = StringIO()
        sys.stdout = captured_output

        log.setup_logging(
            process_name="test-process",
            mouse_id="mouse123",
            session_name="session-abc",
            send_start_log=False
        )

        logging.info("Log message without start log")

        # Restore sys.stdout
        sys.stdout = sys.__stdout__

        # Check captured output
        captured_content = captured_output.getvalue()
        self.assertIn("Log message without start log", captured_content)
