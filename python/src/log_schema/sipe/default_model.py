from typing import Optional

from pydantic import Field, computed_field

from log_schema.defaults.default_model import AINDLogFields


class SIPELogFields(AINDLogFields):
    # Intentionally widens the base `str` field to Optional so SIPE logs don't require it.
    acquisition_name: Optional[str] = Field(  # type: ignore[assignment]
        default=None,
        description=(
            "Unique name of session defined as `<subject_id>_<acquisition-date>_<acquisition-time>`"
        ),
        examples=["123456_2026-01-01_23-00-00"],
    )
    rig_id: Optional[str] = Field(
        default=None,
        description="Name of the software application",
        examples=["FRG.0"],
        validation_alias="aibs_rig_id",
    )
    comp_id: Optional[str] = Field(
        default=None,
        description="Name of the software application",
        examples=["FRG.0-A"],
        validation_alias="aibs_comp_id",
    )

    ################################################################################
    # Renamed fields
    ################################################################################

    # Add additional field where `version` = `software_version`
    @property
    @computed_field
    def version(self) -> Optional[str]:
        return self.software_version

    # Add additional field where `project` = `software_name`
    @property
    @computed_field
    def project(self) -> Optional[str]:
        return self.software_name

    # # Rename software_version to version
    # software_version: Optional[str] = Field(
    #     default=None,
    #     serialization_alias="version",
    # )

    model_config = {"extra": "allow", "serialize_by_alias": True}
