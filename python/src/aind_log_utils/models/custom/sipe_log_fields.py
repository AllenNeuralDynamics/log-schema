from pydantic import Field
from pydantic_settings import BaseSettings


class SipeLogFields(BaseSettings):
    hostname: str | None = Field(
        default=None,
        validation_alias="COMPUTERNAME",
    )
    software_name: str | None = Field(
        default=None,
        description="Name of the software application",
        examples=["stagewidget"],
    )
    software_version: str | None = Field(default=None)
    instrument_id: str | None = Field(default=None, validation_alias="aibs_comp_id")

    model_config = {
        "extra": "allow",
    }
