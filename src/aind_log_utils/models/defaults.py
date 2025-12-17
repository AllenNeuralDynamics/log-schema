import os
from pydantic import BaseModel, Field


def field_from_env():
    try:
        full_rig_id = os.getenv("aibs_comp_id", None)
        rig_part, comp = full_rig_id.split("-", 1)
        rig, instance_str = rig_part.split(".", 1)
        instance = int(instance_str)
        return rig, comp, instance
    except Exception:
        return None, None, None


class DefaultLogFields(BaseModel):
    """
    Base logging fields used for all logs. Provides common context for software, rig, and component.
    """

    software: str | None = Field(
        default=None,
        description="Name of the software application",
        examples=["stagewidget"],
    )
    rig_id: str | None = Field(
        default_factory=lambda: field_from_env()[0],
        description="Rig ID",
        examples=["FRG"],
    )
    comp_id: str | None = Field(
        default_factory=lambda: field_from_env()[1],
        description="Computer ID",
        examples=["A"],
    )
    instance: int | None = Field(
        default_factory=lambda: field_from_env()[2],
        description="Instance number",
        examples=["1"],
    )
    hostname: str | None = Field(
        default_factory=lambda: os.getenv("HOSTNAME", None),
        description="Computer Host Name",
        examples=["DT700413"],
    )

    @staticmethod
    def patch(record):
        # Use this model if one wasn't given
        if "model" not in record["extra"]:
            record["extra"]["model"] = DefaultLogFields()
            # ADD ADDITIONAL LOGIC HERE

        # If field does not exist in record["extra"], add it from model
        # If field already exists, do not overwrite
        for key, value in (
            record["extra"]["model"].model_dump(exclude_none=True).items()
        ):
            record["extra"].setdefault(key, value)

        # Delete [extra][model] field
        del record["extra"]["model"]

        return record
