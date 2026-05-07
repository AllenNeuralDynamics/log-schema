import logging
from pathlib import Path

from aind_log_utils import setup_logging

CONFIG_PATH = Path(__file__).resolve().parent / "configs" / "micestro.yml"


def micestro_mock():
    # Micestro starts
    #   1) Get experiment_type somehow
    #   2) Get session_id
    #   3) Set session_id as environment variable
    #       (this is for bonsai subprocess to know what session its in)
    #   4) Setup logging with those fields

    micestro_log_fields = {
        "software_name": "micestro",
        "software_version": "0.1.0",
        "rig_id": "FRG_1_FAKE",
        "experiment_type": "dynamic_foraging",
        "session_id": "1234",
    }

    """ Loki Labels
    rig_id
    experiment_type
    software_name
    """

    setup_logging(path_to_config=CONFIG_PATH, model=micestro_log_fields)

    logging.info("Micestro starts", extra={"event_type": "stage_start"})

    logging.info("Launching Bonsai")

    logging.info("Starting task generation")
    # This runs in bonsai, it will log its own file (correlates to this through the session_id that
    # was set as an environment variable before launching bonsai)
    logging.info("Finished task generation")

    logging.info("Starting task curriculum")
    # This is a different python package (make sure to configure to read session_id)
    logging.info("Finished task curriculum")

    logging.info("Starting task data mapper")
    # This is a different python package (make sure to configure to read session_id)
    logging.info("Finished task data mapper")

    logging.info("Starting task waterlog")
    # This is a different python package (make sure to configure to read session_id)
    logging.info("Finished task waterlog")

    logging.info("Micestro ends", extra={"event_type": "stage_end"})


def main():
    micestro_mock()


if __name__ == "__main__":
    main()
