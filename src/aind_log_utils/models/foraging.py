from pydantic import Field

from aind_log_utils.models.defaults import DefaultLogFields

class ForagingLogFields(DefaultLogFields):
    """
    Log fields specific to foraging 
    """

    @staticmethod
    def get_subject_id_from_lims(): 
        print("... doot doot doot, eee errr eeeee, wah wah wah, krdng krdng ...")
        print("... getting mouse id from lims ...")
        return 614713

    subject_id: int | None = Field(
        default_factory=get_subject_id_from_lims,
        description="Mouse ID",
        examples=["614173"],
    )
    scientist: str = Field(
        default="Science McGee",
        description="Scientist running curriculum",
        examples=["Science McGee"],
    )

    @staticmethod
    def patch(record):
        # Use this model if one wasn't given
        if "model" not in record["extra"]:
            record["extra"]["model"] = ForagingLogFields()
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

