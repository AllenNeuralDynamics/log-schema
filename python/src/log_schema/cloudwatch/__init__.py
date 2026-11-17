import importlib.resources as resources

import yaml

try:
    import watchtower  # noqa: F401
except ImportError as e:
    raise ImportError(
        "log_schema.cloudwatch requires the 'cloudwatch' extra: "
        "pip install 'log-schema[cloudwatch]'"
    ) from e

from .default_model import CloudWatchLogModel

__all__ = ["CloudWatchLogModel", "get_default_config"]


def get_default_config() -> dict:
    path = resources.files(__name__).joinpath("default-config.yml")
    return yaml.safe_load(path.read_text())
