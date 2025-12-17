from pydantic import BaseModel, Field


class AWSLogFields(BaseModel):
    """
    Log fields specific to AWS logs.
    """

    aws_region: str | None = Field(
        default=None,
        description="Name of aws region",
        examples=["us-west-1"],
    )
    aws_service: str | None = Field(
        default=None,
        description="Name of aws service",
        examples=["s3"],
    )

    @staticmethod
    def patch(record):
        # Use this model if one wasn't given
        if "model" not in record["extra"]:
            record["extra"]["model"] = AWSLogFields()
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


