import importlib.resources as resources

import yaml

try:
    import opentelemetry.sdk  # noqa: F401
except ImportError as e:
    raise ImportError(
        "log_schema.sipe requires the 'otel' extra: pip install 'log-schema[otel]'"
    ) from e

from .default_model import SIPELogFields

__all__ = ["SIPELogFields", "get_default_config"]


def get_default_config() -> dict:
    path = resources.files(__name__).joinpath("default-logging-config.yml")
    return yaml.safe_load(path.read_text())
