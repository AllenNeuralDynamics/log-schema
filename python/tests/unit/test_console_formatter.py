import sys

from dateutil import parser

from log_schema import ConsoleFormatter
from tests.helpers.records import make_record


def test_console_formatter_default_format():
    """
    Tests: ConsoleFormatter with no template.
    Expect: a single line matching the default template: timestamp | padded level | message.
    """
    output = ConsoleFormatter().format(make_record("Test log message"))

    timestamp, level, message = output.split(" | ")

    assert parser.isoparse(timestamp).tzinfo is not None
    assert level == "INFO".ljust(8)
    assert message == "Test log message"


def test_console_formatter_skips_missing_fields():
    """
    Tests: a template that references a field which doesn't exist on the log record.
    Expect: no error; the missing field renders as empty text and its name never appears.
    """
    formatter = ConsoleFormatter(
        template="%(timestamp)s | %(level)-8s | %(message)s | %(fake_field)s"
    )

    output = formatter.format(make_record("Test log message"))

    timestamp, level, message, fake_field = output.split(" | ")

    assert parser.isoparse(timestamp).tzinfo is not None
    assert level == "INFO".ljust(8)
    assert message == "Test log message"
    assert fake_field == ""
    assert "fake_field" not in output


def test_console_formatter_template_handles_old_and_renamed_fields():
    """
    Tests: a template that references both old and renamed fields.
    Expect: the formatter correctly handles both types of fields without error.
    """
    # asctime is the old name of timestamp; level is the renamed levelname
    formatter = ConsoleFormatter(template="%(asctime)s | %(level)-8s | %(levelname)s")

    output = formatter.format(make_record("Test log message"))

    timestamp, level, levelname = output.split(" | ")

    assert parser.isoparse(timestamp).tzinfo is not None
    assert level == "INFO".ljust(8)
    assert levelname == "INFO"


def test_console_formatter_can_select_static_and_extra_fields():
    """
    Tests: a template that selects specific static and extra fields.
    Expect: the formatter outputs only the selected static and extra fields, ignores other.
    """
    # Template selects 1 static field and 1 extra field
    #   Will ignore one of the static fields (`env`)
    #   Will ignore one of the extra fields (`extra_field_2`)
    formatter = ConsoleFormatter(
        template="%(app_name)s | %(extra_field_1)s",
        static_fields={"app_name": "my_app", "env": "production"},
    )

    output = formatter.format(
        make_record("Test log message", extra_field_1="value_1", extra_field_2="value_2")
    )

    assert output == "my_app | value_1"


def test_console_formatter_keeps_traceback():
    """
    Tests: a record with exception info.
    Expect: the log line comes first, followed by the traceback on the next lines.
    """
    formatter = ConsoleFormatter(template="%(message)s")
    record = make_record("hello")
    try:
        raise ValueError("boom")
    except ValueError:
        record.exc_info = sys.exc_info()

    output = formatter.format(record)

    assert output.startswith("hello\n")
    assert "ValueError: boom" in output
