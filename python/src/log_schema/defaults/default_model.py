import socket
from enum import Enum
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class EventType(str, Enum):
    """Canonical event_type values (AIND logging standard).

    Per-event field: pass via the log call's extra, e.g.
    logging.info("starting", extra={"event_type": EventType.STAGE_START}).
    """

    STAGE_START = "stage_start"
    STAGE_COMPLETE = "stage_complete"
    STAGE_FAILURE = "stage_failure"


class AINDLogFields(BaseSettings):
    acquisition_name: str = Field(
        description=(
            "Unique name of session defined as `<subject_id>_<acquisition-date>_<acquisition-time>`"
        ),
        examples=["123456_2026-01-01_23-00-00"],
    )
    hostname: Optional[str] = Field(
        default_factory=socket.gethostname,
        validation_alias="COMPUTERNAME",
        description="Hostname of the machine running software",
        examples=["w10dt700140"],
    )
    event_type: Optional[EventType] = Field(
        default=None,
        description=(
            "Values are `stage_start`, `stage_complete` or `stage_failure` and only injected at "
            "the start and stop of a process/application or on a failure"
        ),
        examples=["stage_start", "stage_complete", "stage_failure"],
    )
    software_name: Optional[str] = Field(
        default=None,
        description="The software generating the logs",
        examples=["waterlog", "aind-data-schema"],
    )
    software_version: Optional[str] = Field(
        default=None,
        description="Version of the software generating the logs",
        examples=["1.0.4.dev0"],
    )
    rig_id: Optional[str] = Field(
        default=None,
        description=(
            "SIPE's naming convention for rigs/machines. Commonly found as an environment "
            "variable called `aibs_comp_id` on the machine"
        ),
        examples=["frg_1_a", "ephys_9_acq"],
    )
    instrument_id: Optional[str] = Field(
        default=None,
        description=(
            "Scientific Computing's convention for instruments. Definition can be found at "
            "https://aind-data-schema.readthedocs.io/en/latest/instrument.html"
        ),
        examples=["MESO1", "EPHYS1"],
    )
    subject_id: Optional[str] = Field(
        default=None,
        description="Subject ID (Unique identifier for the subject of data acquisition)",
        examples=["123456"],
    )
    specimen_id: Optional[str] = Field(
        default=None,
        description=(
            "An identifier for a tissue removed from a subject and should include the "
            "`subject_id` in the name"
        ),
        examples=["123456", "123456_001"],
    )
    pipeline_name: Optional[str] = Field(
        default=None,
        description="Name of pipeline processing, transforming and/or QC'ing raw data",
        examples=["codeocean pipeline", "airflow DAG"],
    )
    process_name: Optional[str] = Field(
        default=None,
        description="Name of container processing, transforming and/or QC'ing raw data",
        examples=["code ocean capsule"],
    )
    user_id: Optional[str] = Field(
        default=None,
        description=(
            "User running software. Intended specifically for software which run experiments "
            "to indicate who is running the experiment"
        ),
    )

    model_config = {
        "extra": "allow",
    }
