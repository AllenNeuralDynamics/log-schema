""" Tests for the log utility functions """
import logging
import os
from unittest import mock, TestCase
from aind_log_utils import log
from io import StringIO
from botocore.exceptions import ClientError


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
                 "CO_CAPSULE_ID": "test-capsule-id"
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
        self.assertEqual(metadata["capsule_id"], "test-capsule-id")
        self.assertNotEqual(metadata["log_session"], "")

    def test_make_record_factory(self):
        """
        Test that the record factory is correctly created
        """
        metadata = {
            "hostname": "test-host",
            "comp_id": "test-comp-id",
            "capsule_id": "test-cap-id",
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
        self.assertEqual(record.version, "test-cap-id")
        self.assertEqual(record.log_session, "test-session")
        self.assertEqual(record.mouse_id, "mouse123")
        self.assertEqual(record.session_name, "session-abc")
        self.assertEqual(record.process_name, "test-process")

    def test_nonaws_setup_logging(self):
        """
        Test that the logger is correctly set up without sending the start log
        """
        captured_output = StringIO()

        # This is the line an external user would call
        log.setup_logging(
            process_name="test-process",
            mouse_id="mouse123",
            session_name="session-abc"
        )

        # This is internal code to fetch the log for the test.
        # We add a StreamHandler to capture the log output.
        logger = logging.getLogger()
        stream_handler = logging.StreamHandler(captured_output)
        logger.addHandler(stream_handler)
        logger.setLevel(logging.INFO)

        # This is the line an external user would call
        logging.warning("Log message without start log")

        stream_handler.flush()

        # Check captured output
        captured_content = captured_output.getvalue()

        self.assertIn("Log message without start log", captured_content)

    @mock.patch('aind_log_utils.log.check_aws_credentials', return_value=True)
    @mock.patch('boto3.client')
    def test_aws_setup_logging(self, mock_boto3_client, mock_check_aws_credentials):
        """
        Test that the logger is correctly set up with mocked AWS environment
        """
        captured_output = StringIO()

        # Mock AWS credentials (dummy values)
        mock_aws_credentials = mock.Mock()
        mock_aws_credentials.access_key = "mock-access-key"
        mock_aws_credentials.secret_key = "mock-secret-key"

        # Mock get_credentials to return dummy credentials
        mock_boto3_client.return_value.get_credentials.return_value = mock_aws_credentials

        # Create a more realistic mock for paginator and result_keys
        mock_result_key = mock.Mock()
        mock_result_key.parsed = {"value": "logGroups"}  # Mimics the expected parsed structure

        mock_paginator = mock.Mock()
        mock_paginator.result_keys = [mock_result_key]
        # Mocking result_keys as a list of objects
        mock_paginator.paginate.return_value = [{'logGroups': [{'logGroupName': 'test-log-group'}]}]
        mock_boto3_client.return_value.get_paginator.return_value = mock_paginator

        # Mock other attributes or methods if necessary
        mock_boto3_client.return_value.exceptions.ClientError = ClientError

        # Call setup_logging with a message
        message_template = "Test"
        subject_id = "999999"
        session_name = f"{subject_id}-110824"

        log.setup_logging(
            process_name="test-capsule",
            mouse_id=subject_id,
            session_name=session_name,
            send_start_log=False,
        )

        # This is internal code to fetch the log for the test.
        # We add a StreamHandler to capture the log output.
        logger = logging.getLogger()
        stream_handler = logging.StreamHandler(captured_output)
        logger.addHandler(stream_handler)
        logger.setLevel(logging.INFO)

        logging.info(message_template)

        stream_handler.flush()

        # Check captured output
        captured_content = captured_output.getvalue()
        expected_substrings = session_name
        self.assertIn(expected_substrings, captured_content)

        # Verify that the paginator was used
        mock_boto3_client.return_value.get_paginator.assert_called_once()
        mock_paginator.paginate.assert_called_once_with(logGroupNamePrefix='aind/internal_logs')

    @mock.patch('boto3.Session')
    def test_check_aws_credentials(self, mock_session):
        """
        Test the check_aws_credentials function.
        """
        # Mock a session with valid credentials
        mock_credentials = mock.Mock()
        mock_credentials.access_key = "valid-access-key"
        mock_credentials.secret_key = "valid-secret-key"
        mock_credentials.token = "valid-token"

        mock_session_instance = mock.Mock()
        mock_session_instance.get_credentials.return_value = mock_credentials
        mock_session_instance.client.return_value.get_caller_identity.return_value = {
            "UserId": "test-user",
            "Account": "test-account",
            "Arn": "arn:aws:iam::test-account:user/test-user"
        }
        mock_session.return_value = mock_session_instance

        # Test with valid credentials
        self.assertTrue(log.check_aws_credentials())

        # Mock a session with missing credentials
        mock_session_instance.get_credentials.return_value = None
        self.assertFalse(log.check_aws_credentials())
