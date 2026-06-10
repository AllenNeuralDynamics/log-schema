from __future__ import annotations

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class SipeLogFields(BaseSettings):
    hostname: Optional[str] = Field(
        default=None,
        validation_alias="COMPUTERNAME",
    )
    software_name: Optional[str] = Field(
        default=None,
        description="Name of the software application",
        examples=["stagewidget"],
    )
    software_version: Optional[str] = Field(default=None)
    instrument_id: Optional[str] = Field(default=None, validation_alias="aibs_comp_id")

    model_config = {
        "extra": "allow",
    }
