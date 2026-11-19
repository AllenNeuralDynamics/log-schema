from typing import Optional

from pydantic import BaseModel


class CloudWatchLogModel(BaseModel):
    service: Optional[str] = None
    environment: Optional[str] = None

    model_config = {
        "extra": "allow",
    }
