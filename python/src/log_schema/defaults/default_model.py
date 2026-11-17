import socket
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class AINDLogFields(BaseSettings):
    software_name: str = Field(
        description="Name of the software application", examples=["micestro"]
    )
    software_version: str = Field(
        description="Version of the software application", examples=["1.0.0"]
    )
    hostname: Optional[str] = Field(
        default_factory=socket.gethostname, validation_alias="COMPUTERNAME"
    )

    model_config = {
        "extra": "allow",
    }
