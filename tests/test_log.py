"""Tests for aind_log_utils.log module."""

import json
import logging
import os
import sys
import tempfile
import textwrap
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from aind_log_utils.log import (
    AindContextFilter,
    AindJsonFormatter,
    add_cloudwatch_handler,
    setup_logging_cloudwatch,
)

MINIMAL_LOGGING_YML = textwrap.dedent("""\
    version: 1
    disable_existing_loggers: false
    filters:
      aind_fields:
        (): aind_log_utils.log.AindContextFilter
        acquisition_name: "undefined"
    formatters:
      json:
        (): aind_log_utils.log.AindJsonFormatter
    handlers:
      console:
        class: logging.StreamHandler
        formatter: json
        filters: [aind_fields]
        stream: ext://sys.stdout
    root:
      level: DEBUG
      handlers: [console]
    """)


def _make_record(msg="hello", level=logging.INFO, exc_info=None, **kwargs):
    record = logging.LogRecord(
        name="test",
        level=level,
        pathname="",
        lineno=0,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )
    for k, v in kwargs.items():
        setattr(record, k, v)
    return record


class TestAindJsonFormatterDefaultFields(unittest.TestCase):
    """AindJsonFormatter with default field list."""

    def setUp(self):
        self.formatter = AindJsonFormatter()

    def test_default_field_list(self):
        """Default fields include timestamp, level, message,
        acquisition_name."""
        self.assertEqual(
            self.formatter.fields,
            ["timestamp", "level", "message", "acquisition_name"],
        )

    def test_timestamp_is_iso8601(self):
        """timestamp is a parseable ISO 8601 string."""
        record = _make_record(acquisition_name="acq")
        result = json.loads(self.formatter.format(record))
        datetime.fromisoformat(result["timestamp"])  # raises if invalid

    def test_level_field(self):
        """level maps to record.levelname."""
        record = _make_record(level=logging.WARNING, acquisition_name="acq")
        result = json.loads(self.formatter.format(record))
        self.assertEqual(result["level"], "WARNING")

    def test_message_field(self):
        """message maps to record.getMessage()."""
        record = _make_record(msg="hello %s", acquisition_name="acq")
        record.args = ("world",)
        result = json.loads(self.formatter.format(record))
        self.assertEqual(result["message"], "hello world")

    def test_custom_attribute_present(self):
        """A custom field already on the record is read directly."""
        record = _make_record(acquisition_name="session-42")
        result = json.loads(self.formatter.format(record))
        self.assertEqual(result["acquisition_name"], "session-42")

    def test_custom_attribute_missing_defaults_to_undefined(self):
        """A custom field absent from the record defaults to 'undefined'."""
        record = _make_record()  # no acquisition_name
        result = json.loads(self.formatter.format(record))
        self.assertEqual(result["acquisition_name"], "undefined")

    def test_exc_info_included_when_present(self):
        """exc_info key is added when the record carries exception info."""
        try:
            raise ValueError("boom")
        except ValueError:
            exc = sys.exc_info()
        record = _make_record(exc_info=exc, acquisition_name="acq")
        result = json.loads(self.formatter.format(record))
        self.assertIn("exc_info", result)
        self.assertIn("ValueError", result["exc_info"])

    def test_exc_info_absent_when_none(self):
        """exc_info key is omitted when there is no exception."""
        record = _make_record(acquisition_name="acq")
        result = json.loads(self.formatter.format(record))
        self.assertNotIn("exc_info", result)


class TestAindJsonFormatterCustomFields(unittest.TestCase):
    """AindJsonFormatter with a custom field list."""

    def test_required_fields_always_present(self):
        """Required fields are always included even when
        omitted from custom list."""
        formatter = AindJsonFormatter(fields=["level", "message"])
        record = _make_record()
        result = json.loads(formatter.format(record))
        self.assertSetEqual(
            set(result.keys()),
            {"timestamp", "level", "message", "acquisition_name"},
        )

    def test_extra_custom_fields_included(self):
        """Fields beyond the required set are included when requested."""
        formatter = AindJsonFormatter(fields=["lineno", "level", "message"])
        record = _make_record()
        result = json.loads(formatter.format(record))
        self.assertIn("lineno", result)

    def test_non_standard_logrecord_attribute(self):
        """Standard LogRecord attributes (e.g. lineno) are read correctly."""
        formatter = AindJsonFormatter(fields=["lineno"])
        record = logging.LogRecord(
            name="t",
            level=logging.DEBUG,
            pathname="f.py",
            lineno=99,
            msg="m",
            args=(),
            exc_info=None,
        )
        result = json.loads(formatter.format(record))
        self.assertEqual(result["lineno"], 99)


class TestAindContextFilter(unittest.TestCase):
    """Tests for AindContextFilter."""

    def test_injects_all_configured_fields(self):
        """All fields passed to the constructor are set on the record."""
        f = AindContextFilter(acquisition_name="acq-1", process_name="cap")
        record = _make_record()
        f.filter(record)
        self.assertEqual(record.acquisition_name, "acq-1")
        self.assertEqual(record.process_name, "cap")

    def test_does_not_override_existing_field(self):
        """Fields already present on the record are left unchanged."""
        f = AindContextFilter(acquisition_name="default")
        record = _make_record(acquisition_name="per-call-override")
        f.filter(record)
        self.assertEqual(record.acquisition_name, "per-call-override")

    def test_always_returns_true(self):
        """filter() never drops records (always returns True)."""
        f = AindContextFilter(acquisition_name="x")
        self.assertTrue(f.filter(_make_record()))

    def test_no_fields_configured(self):
        """Works correctly when constructed with no fields."""
        f = AindContextFilter()
        record = _make_record()
        self.assertTrue(f.filter(record))


class TestAddCloudwatchHandler(unittest.TestCase):
    """Tests for add_cloudwatch_handler."""

    def _save_and_clear_root_handlers(self):
        root = logging.getLogger()
        saved = root.handlers[:]
        root.handlers.clear()
        return saved

    def _restore_root_handlers(self, saved):
        root = logging.getLogger()
        root.handlers = saved

    def test_warns_and_returns_when_watchtower_missing(self):
        """Logs a warning and exits early when watchtower cannot
        be imported."""
        with patch.dict(sys.modules, {"watchtower": None}):
            with self.assertLogs(level="WARNING") as cm:
                add_cloudwatch_handler("stream")
        self.assertTrue(any("watchtower" in line for line in cm.output))

    def test_creates_handler_with_correct_arguments(self):
        """CloudWatchLogHandler is constructed with the right stream
         and group."""
        mock_wt = MagicMock()
        mock_handler = MagicMock()
        mock_wt.CloudWatchLogHandler.return_value = mock_handler

        saved = self._save_and_clear_root_handlers()
        try:
            with patch.dict(sys.modules, {"watchtower": mock_wt}):
                add_cloudwatch_handler("my-stream")
        finally:
            self._restore_root_handlers(saved)

        mock_wt.CloudWatchLogHandler.assert_called_once_with(
            log_stream_name="my-stream",
            log_group="aind/internal-logs",
        )

    def test_reuses_existing_aind_json_formatter(self):
        """Reuses the AindJsonFormatter already attached to a
        console handler."""
        mock_wt = MagicMock()
        mock_handler = MagicMock()
        mock_wt.CloudWatchLogHandler.return_value = mock_handler

        existing_formatter = AindJsonFormatter()
        console = logging.StreamHandler()
        console.setFormatter(existing_formatter)

        saved = self._save_and_clear_root_handlers()
        logging.getLogger().addHandler(console)
        try:
            with patch.dict(sys.modules, {"watchtower": mock_wt}):
                add_cloudwatch_handler("stream")
        finally:
            self._restore_root_handlers(saved)

        mock_handler.setFormatter.assert_called_once_with(existing_formatter)

    def test_copies_existing_aind_context_filter(self):
        """Copies AindContextFilter from an existing handler onto
        the CW handler."""
        mock_wt = MagicMock()
        mock_handler = MagicMock()
        mock_wt.CloudWatchLogHandler.return_value = mock_handler

        existing_filter = AindContextFilter(acquisition_name="acq")
        console = logging.StreamHandler()
        console.addFilter(existing_filter)

        saved = self._save_and_clear_root_handlers()
        logging.getLogger().addHandler(console)
        try:
            with patch.dict(sys.modules, {"watchtower": mock_wt}):
                add_cloudwatch_handler("stream")
        finally:
            self._restore_root_handlers(saved)

        mock_handler.addFilter.assert_called_once_with(existing_filter)

    def test_falls_back_to_new_formatter_when_none_found(self):
        """Creates a fresh AindJsonFormatter when no
        existing handler has one."""
        mock_wt = MagicMock()
        mock_handler = MagicMock()
        mock_wt.CloudWatchLogHandler.return_value = mock_handler

        saved = self._save_and_clear_root_handlers()
        try:
            with patch.dict(sys.modules, {"watchtower": mock_wt}):
                add_cloudwatch_handler("stream")
        finally:
            self._restore_root_handlers(saved)

        mock_handler.setFormatter.assert_called_once()
        self.assertIsInstance(
            mock_handler.setFormatter.call_args[0][0], AindJsonFormatter
        )

    def test_handler_is_added_to_root_logger(self):
        """The new handler is added to the root logger."""
        mock_wt = MagicMock()
        mock_handler = MagicMock()
        mock_wt.CloudWatchLogHandler.return_value = mock_handler

        saved = self._save_and_clear_root_handlers()
        try:
            with patch.dict(sys.modules, {"watchtower": mock_wt}):
                add_cloudwatch_handler("stream")
            self.assertIn(mock_handler, logging.getLogger().handlers)
        finally:
            self._restore_root_handlers(saved)


class TestSetupLogging(unittest.TestCase):
    """Tests for setup_logging_cloudwatch."""

    def tearDown(self):
        logging.getLogger().handlers.clear()

    def test_fallback_to_basicconfig_when_yml_missing(self):
        """Falls back to basicConfig and warns when logging.yml is absent."""
        with patch("aind_log_utils.log._CONFIG_PATH", "/nonexistent/path.yml"):
            with patch("aind_log_utils.log.add_cloudwatch_handler") as mock_cw:
                with self.assertLogs(level="WARNING") as cm:
                    setup_logging_cloudwatch("stream")

        self.assertTrue(any("logging.yml" in line for line in cm.output))
        mock_cw.assert_called_once_with(log_stream="stream")

    def test_loads_yml_and_applies_extra_fields(self):
        """Loads logging.yml and injects extra fields into the
        aind_fields filter."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as f:
            f.write(MINIMAL_LOGGING_YML)
            tmp_path = f.name

        try:
            with patch("aind_log_utils.log._CONFIG_PATH", tmp_path):
                with patch(
                    "aind_log_utils.log.add_cloudwatch_handler"
                ) as mock_cw:
                    setup_logging_cloudwatch(
                        "my-stream", acquisition_name="acq-999"
                    )

            mock_cw.assert_called_once_with(log_stream="my-stream")

            # Confirm the filter on the console handler carries the
            # injected field
            root = logging.getLogger()
            injected = {
                k: v
                for handler in root.handlers
                for f in handler.filters
                if isinstance(f, AindContextFilter)
                for k, v in f.fields.items()
            }
            self.assertEqual(injected.get("acquisition_name"), "acq-999")
        finally:
            os.unlink(tmp_path)
            logging.getLogger().handlers.clear()


if __name__ == "__main__":
    unittest.main()
