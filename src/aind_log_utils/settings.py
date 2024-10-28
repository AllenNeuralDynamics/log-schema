import datetime
import importlib
import inspect
import os
import pathlib
import platform
import sys
from functools import cached_property
from getpass import getuser
from hashlib import md5
from importlib import metadata
from typing import Union

from pydantic import (
    AliasChoices,
    Field,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="aind_log_utils"
    )  # , extra='allow')

    project_name: str = Field("undefined")
    comp_id: str = Field(
        "N/A", validation_alias=AliasChoices("aibs_comp_id", "aind_comp_id")
    )
    dev_mode: bool = Field(False)
    hostname: str = platform.uname().node
    user_name: str = getuser()

    @computed_field
    @property
    def log_config_file(self) -> os.PathLike:
        return self.project_path / "logs" / f"{self.project_name}.yml"

    @computed_field
    @property
    def version(self) -> str:
        try:
            frame = sys._getframe(2)
            module = inspect.getmodule(frame)
            version = importlib.metadata.version(module.__package__)
        except:
            # Probably a 1 off script that's not installed so it likely won't have a version
            version = "N/A"
        return version

    @computed_field
    @cached_property
    def project_path(self) -> Union[str, os.PathLike]:
        if "windows" in platform.uname().system.lower():
            path = f"c:/ProgramData/AIND/"
        else:
            path = os.path.expandvars(f"~/.config/AIND/")
        return pathlib.Path(path)

    @computed_field
    @cached_property
    def session_id(self) -> str:
        session_parts = [
            str(datetime.datetime.now()),
            platform.node(),
            str(os.getpid()),
        ]
        return md5(("".join(session_parts)).encode("utf-8")).hexdigest()[:7]
