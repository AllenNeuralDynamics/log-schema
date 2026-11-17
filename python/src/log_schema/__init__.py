from ._setup_base import DefaultFormatter, StaticFieldsFilter, setup_logging
from ._setup_otel import otel_log_handler, setup_logging_otel

__all__ = [
    "setup_logging",
    "DefaultFormatter",
    "StaticFieldsFilter",
    "setup_logging_otel",
    "otel_log_handler",
]
