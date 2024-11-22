import atexit
import datetime
import logging
import logging.config
import logging.handlers
import os
import platform
import sys
import traceback
from hashlib import md5
from importlib import resources
import yaml


def make_record_factory(log_metadata):
    # We start with the base factory
    log_record_factory = (
        logging.getLogRecordFactory()
    )

    def record_factory(*args, **kwargs):

        record = log_record_factory(*args, **kwargs)
        # We add the items that we need to track across AIND

        record.exc_info = sys.exc_info()
        record.exc_text = traceback.format_exc()

        record.hostname = log_metadata.get('hostname', 'undefined')
        record.comp_id = log_metadata.get('comp_id', 'undefined')
        record.version = log_metadata.get('version', 'undefined')
        record.log_session = log_metadata.get('log_session', 'undefined')
        record.user_name = log_metadata.get('user_name', 'undefined')
        record.mouse_id = log_metadata.get('mouse_id', 'undefined')
        record.session_name = log_metadata.get('session_name', 'undefined')
        record.process_name = log_metadata.get('process_name', 'undefined')

        return record
    return record_factory


def prepare_metadata(process_name, mouse_id, session_name):
    log_metadata = {}

    # First metadata shared across all AIND processes. Those are the most
    # important ones.
    log_metadata['process_name'] = process_name
    log_metadata['mouse_id'] = mouse_id
    log_metadata['session_name'] = session_name

    # To ensure that we can track logs from a single session
    session_parts = [str(datetime.datetime.now()),
                     platform.node(), str(os.getpid())]
    log_metadata['log_session'] = md5((''.join(session_parts)).
                                      encode("utf-8")).hexdigest()[:7]
    log_metadata['hostname'] = os.getenv("HOSTNAME", "undefined")
    log_metadata['comp_id'] = os.getenv("CO_COMPUTATION_ID", "undefined")
    log_metadata['version'] = os.getenv("CO_CAPSULE_ID", "undefined")
    log_metadata['process_name'] = process_name

    return log_metadata


def setup_logging(
    process_name: str,
    mouse_id: str = 'undefined',
    session_name: str = 'undefined',
    send_start_log: bool = True,
):
    """
    Logging setup consists of
      1.  applying the logging configuration to the Python logging module
      2.  injecting additional data into the log records via the log factory
      3.  sending a start log and registering to send a stop log
    :param process_name: The name of the process to track
    :param mouse_id: The mouse ID to track
    :param session_name: The session name to track
    :param send_start_log: Whether to send a log to the webserver
    (not desirable for libraries) [default = True]
    """
    log_config = yaml.safe_load(resources.read_text("aind_log_utils", 
                                                    "default_logging.yml"))

    log_metadata = prepare_metadata(process_name,
                                    mouse_id, session_name)

    logging.setLogRecordFactory(make_record_factory(log_metadata))

    logging.config.dictConfig(log_config)

    if send_start_log:
        logging.info("Starting")
        atexit.register(lambda: logging.info("Stopping"))
