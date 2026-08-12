from ._setup_base import DefaultFormatter, setup_logging
from ._setup_otel import setup_logging_otel

__all__ = ["setup_logging", "DefaultFormatter", "setup_logging_otel", "__version__"]
