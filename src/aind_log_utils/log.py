""" This file is the main file for the aind-log-utils package. It contains the
functions that are meant to be used by the users of the package.
"""

import atexit
import datetime
import logging
import logging.config
import logging.handlers
import os
import platform
from hashlib import md5

import boto3


def check_aws_credentials():
    """
    This function checks if the AWS credentials are valid.
    :return: True if the credentials are valid, False otherwise
    """
    session = boto3.Session()
    credentials = session.get_credentials()
    if not credentials or not credentials.access_key:
        logging.warning("AWS credentials not found.")
        return False
    else:
        sts = session.client("sts")
        sts.get_caller_identity()
        logging.info("AWS credentials are valid.")
        return True


def make_record_factory(log_metadata):
    """
    This function creates a log record factory that adds metadata to the log
    records. This metadata is shared across all AIND code ocean processes.
    :param log_metadata: A dictionary with the metadata to add to the log
    records
    :return: A log record factory that adds the metadata to the log records
    """
    # We start with the base factory
    log_record_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        """
        This function creates a log record with the metadata added
        :param args: The arguments to pass to the log record factory
        :param kwargs: The keyword arguments to pass to the log record factory
        :return: A log record with the metadata added
        """
        record = log_record_factory(*args, **kwargs)
        # We add the items that we need to track across AIND
        record.hostname = log_metadata.get("hostname", "undefined")
        record.comp_id = log_metadata.get("comp_id", "undefined")
        record.version = log_metadata.get("capsule_id", "undefined")
        record.log_session = log_metadata.get("log_session", "undefined")
        record.user_name = log_metadata.get("user_name", "undefined")
        record.subject_id = log_metadata.get("subject_id", "undefined")
        record.asset_name = log_metadata.get("asset_name", "undefined")
        record.process_name = log_metadata.get("process_name", "undefined")
        record.CO_MEMORY = os.getenv("CO_MEMORY", "undefined")
        record.CO_CPUS = os.getenv("CO_CPUS", "undefined")
        record.AWS_BATCH_JOB_ID = os.getenv("AWS_BATCH_JOB_ID", "undefined")
        record.AWS_BATCH_CE_NAME = os.getenv("AWS_BATCH_CE_NAME", "undefined")
        record.AWS_BATCH_JQ_NAME = os.getenv("AWS_BATCH_JQ_NAME", "undefined")
        record.AWS_METADATA_SERVICE_NUM_ATTEMPTS = os.getenv(
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS", "undefined"
        )
        record.AWS_BATCH_JOB_ATTEMPT = os.getenv(
            "AWS_BATCH_JOB_ATTEMPT", "undefined"
        )
        record.AWS_MAX_ATTEMPTS = os.getenv("AWS_MAX_ATTEMPTS", "undefined")

        return record

    return record_factory


def prepare_metadata(process_name, subject_id, asset_name):
    """
    This function prepares the metadata that is attached to all logs.
    :param process_name: The name of the process to track
    :param subject_id: The subject ID to track
    :param asset_name: The asset name to track
    :return: A dictionary with the metadata to add to the log records
    """

    log_metadata = {}

    # First metadata shared across all AIND processes. Those are the most
    # important ones.
    log_metadata["process_name"] = process_name
    log_metadata["subject_id"] = subject_id
    log_metadata["asset_name"] = asset_name

    # To ensure that we can track logs from a single session
    session_parts = [
        str(datetime.datetime.now()),
        platform.node(),
        str(os.getpid()),
    ]
    log_metadata["log_session"] = md5(
        ("".join(session_parts)).encode("utf-8")
    ).hexdigest()[:7]
    log_metadata["hostname"] = os.getenv("HOSTNAME", "undefined")
    log_metadata["comp_id"] = os.getenv("CO_COMPUTATION_ID", "undefined")
    log_metadata["capsule_id"] = os.getenv("CO_CAPSULE_ID", "undefined")
    log_metadata["process_name"] = process_name

    log_metadata["CO_MEMORY"] = os.getenv("CO_MEMORY", "undefined")
    log_metadata["CO_CPUS"] = os.getenv("CO_CPUS", "undefined")
    log_metadata["AWS_BATCH_JOB_ID"] = os.getenv(
        "AWS_BATCH_JOB_ID", "undefined"
    )
    log_metadata["AWS_BATCH_CE_NAME"] = os.getenv(
        "AWS_BATCH_CE_NAME", "undefined"
    )
    log_metadata["AWS_BATCH_JQ_NAME"] = os.getenv(
        "AWS_BATCH_JQ_NAME", "undefined"
    )
    log_metadata["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = os.getenv(
        "AWS_METADATA_SERVICE_NUM_ATTEMPTS", "undefined"
    )
    log_metadata["AWS_BATCH_JOB_ATTEMPT"] = os.getenv(
        "AWS_BATCH_JOB_ATTEMPT", "undefined"
    )
    log_metadata["AWS_MAX_ATTEMPTS"] = os.getenv(
        "AWS_MAX_ATTEMPTS", "undefined"
    )

    return log_metadata


def setup_logging(
    process_name: str,
    subject_id: str = "undefined",
    asset_name: str = "undefined",
    send_start_log: bool = True,
    disable_existing_loggers: bool = True,
    **kwargs,
):
    """
    Logging setup consists of
      1.  applying the logging configuration to the Python logging module
      2.  injecting additional data into the log records via the log factory
      3.  sending a start log and registering to send a stop log
    :param process_name: The name of the process to track
    :param subject_id: The subject ID to track
    :param asset_name: The asset name to track
    :param send_start_log: Whether to send a log to the webserver
    (not desirable for libraries) [default = True]
    :param disable_existing_loggers: Whether to disable existing loggers
    """

    # Map old parameter names to new ones for backwards compatibility
    old_to_new = {
        "mouse_id": "subject_id",
        "session_name": "asset_name",
    }

    # Check for old parameter names in kwargs
    for old_name, new_name in old_to_new.items():
        if old_name in kwargs:
            logging.warning(
                f"'{old_name}' is deprecated and will be removed in future versions. Use '{new_name}' instead."
            )
            # Use the old parameter value to set the new parameter
            if new_name == "subject_id":
                subject_id = kwargs[old_name]
            elif new_name == "asset_name":
                asset_name = kwargs[old_name]

    if check_aws_credentials():
        # If that passses, we expect to be on Code Ocean
        boto3_logs_client = boto3.client("logs", region_name="us-west-2")
        logging.info("Connected to boto3. Logging to console and cloudwatch")

        log_metadata = prepare_metadata(process_name, subject_id, asset_name)

        log_config = {
            "version": 1,
            "disable_existing_loggers": disable_existing_loggers,
            "root": {
                "level": "INFO",
                "handlers": ["console", "watchtower"],
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",  # Ensure logs go to the expected output stream
                },
                "watchtower": {
                    "class": "watchtower.CloudWatchLogHandler",
                    "boto3_client": boto3_logs_client,
                    "log_group_name": "aind/internal_logs",
                    "log_stream_name": log_metadata["capsule_id"],
                    "level": "INFO",
                },
            },
        }

        logging.setLogRecordFactory(make_record_factory(log_metadata))
        logging.config.dictConfig(log_config)
        logger = logging.getLogger()
        logger.handlers[1].formatter.add_log_record_attrs = [
            "levelname",
            "filename",
            "subject_id",
            "process",
            "thread",
            "lineno",
            "message",
            "hostname",
            "comp_id",
            "version",
            "log_session",
            "user_name",
            "asset_name",
            "process_name",
            "exc_info",
            "exc_text",
            "CO_MEMORY",
            "CO_CPUS",
            "AWS_BATCH_JOB_ID",
            "AWS_BATCH_CE_NAME",
            "AWS_BATCH_JQ_NAME",
            "AWS_METADATA_SERVICE_NUM_ATTEMPTS",
            "AWS_BATCH_JOB_ATTEMPT",
            "AWS_MAX_ATTEMPTS",
        ]
    else:
        log_config = {
            "version": 1,
            "disable_existing_loggers": disable_existing_loggers,
            "root": {
                "level": "INFO",
                "handlers": ["console"],
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                }
            },
        }
        logging.config.dictConfig(log_config)

        # we raise a warning and return
        logging.warning("Could not connect to boto3. Logging to console only")

    if send_start_log:
        logging.info("Starting")
        atexit.register(lambda: logging.info("Stopping"))
