import logging
from pathlib import Path

from log_schema.log_schema_utils import add_log_context, configure_logging

log_schema_dir = Path(__file__).parent.parent / "src" / "log_schema"
configure_logging(
    log_schema_dir / "defaults" / "logging_config.yml.jinja",
    log_file=log_schema_dir / "example.log",
    json_log_file=log_schema_dir / "example.log.jsonl",
)

logging.info("First log before adding static fields")

# Add static fields to the root logger
add_log_context({"software_name": "example", "software_version": "1.0.2"})

logging.info("After context is added")

logging.info(
    "With per-log fields",
    extra={
        "software_name": "a third thing",
        "software_version": "5.6.7",
        "new_field": "this is a new field",
    },
)
add_log_context({"software_name": "SOMETHING ELSE", "software_version": "1.0.2"})

logging.info("After context is changed")
