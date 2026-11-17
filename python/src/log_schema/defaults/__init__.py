import importlib.resources as resources

import yaml

from .default_model import AINDLogFields

__all__ = ["AINDLogFields", "get_default_config"]


def get_default_config() -> dict:
    path = resources.files(__name__).joinpath("default-logging-config.yml")
    return yaml.safe_load(path.read_text())
