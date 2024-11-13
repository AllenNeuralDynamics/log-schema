import atexit
import datetime
import getpass
import importlib.metadata
import inspect
import logging
import logging.config
import logging.handlers
import os
import pathlib
import platform
import sys
import traceback
from hashlib import md5
from importlib import resources
from queue import Queue
import yaml
import json
import boto3


class JsonFormatter(logging.Formatter):
    """Formatter to dump error message into JSON"""

    def format(self, record: logging.LogRecord) -> str:
        record_dict = {
            "level": record.levelname,
            "date": self.formatTime(record),
            "message": record.getMessage(),
            "module": record.module,
            "lineno": record.lineno,
        }
        return json.dumps(record_dict)


def process_path(process_name: str) -> pathlib.Path:
    if path := os.getenv(f'{process_name}_path', None) is None:
        if 'windows' in platform.uname().system.lower():
            path = f'c:/ProgramData/AIND/{process_name}'
        else:
            path = os.path.expandvars('~/.config/AIND/')

    return os.path.expanduser(
        pathlib.Path(path) / "logs" / f"{process_name}.yml")


def load_logging_config(process_name: str) -> dict:
    log_config_file = process_path(process_name)

    if not os.path.exists(log_config_file):
        log_config = yaml.safe_load(resources.read_text("aind_log_utils",
                                                        "default_logging.yml"))
        try:
            os.makedirs(os.path.dirname(log_config_file), exist_ok=True)
            yaml.dump(log_config, open(log_config_file, 'w'))
        except IOError as e:
            print(f"Could not write logging configuration to \
                  {log_config_file}: {e}")
        else:
            print(f"Default logging configuration to {log_config_file}")
    else:
        log_config = yaml.load(open(log_config_file, "r"),
                               Loader=yaml.FullLoader)

    return log_config


def make_record_factory(log_metadata, always_pass_exc_info=False):
    # We start with the base factory
    log_record_factory = (
        logging.getLogRecordFactory()
    )

    def record_factory(*args, **kwargs):

        record = log_record_factory(*args, **kwargs)
        # We add the items that we need to track across AIND

        if not record.exc_info and always_pass_exc_info:
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

def prepare_metadata(logger_name, process_name, mouse_id, session_name): 
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

    # These are the metadata that are specific to the logger
    if logger_name == 'aind_logger':
        log_metadata['hostname'] = platform.uname().node
        log_metadata['comp_id'] = os.getenv("aibs_comp_id", "undefined")
        log_metadata['user_name'] = getpass.getuser()
        try:
            frame = inspect.currentframe().f_back
            module = inspect.getmodule(frame)
            log_metadata['version'] = importlib.metadata.version(
                module.__package__)
        except Exception:
            log_metadata['version'] = 'N/A'
            # Probably a 1 off script that's not installed
            # so it likely won't have a version
    elif logger_name == 'codeocean_logger':
        log_metadata['hostname'] = os.getenv("HOSTNAME", "undefined")
        log_metadata['comp_id'] = os.getenv("CO_COMPUTATION_ID", "undefined")
        log_metadata['version'] = os.getenv("CO_CAPSULE_ID", "undefined")
        log_metadata['process_name'] = process_name

    return log_metadata

def setup_logging(
    process_name: str,
    logger_name = 'codeocean_logger',
    mouse_id: str = 'undefined',
    session_name: str = 'undefined',
    send_start_log: bool = True,
    always_pass_exc_info = False,
):
    """
    Logging setup consists of
      1.  applying the logging configuration to the Python logging module
      2.  injecting additional data into the log records via the log factory
      3.  sending a start log and registering to send a stop log
    :param process_name: The name of the configuration, usually process name,
    you want to find
    :param send_start_log: Whether to send a log to the webserver
    (not desirable for libraries) [default = True]
    :param always_pass_exc_info: whether to always check for exc_info
    """
    log_config = load_logging_config(process_name)

    log_metadata = prepare_metadata(logger_name, process_name, 
                                    mouse_id, session_name)

    # Find file handlers and ensure the path exists to write the log file
    # Also, the default file handler "default_file_handler"
    # is renamed to have the process name in it.
    handlers = log_config["handlers"]
    if "default_file_handler" in handlers:
        handlers["default_file_handler"]["filename"] = handlers[
            "default_file_handler"
        ]["filename"].format(process_name=process_name)

    # Here we prepare the handlers for the loggers
    for handler in handlers.values():
        # Configure all file handlers
        if handler["class"] == "logging.handlers.RotatingFileHandler":
            if "filename" in handler:
                os.makedirs(
                    os.path.dirname(handler["filename"]), exist_ok=True
                )
        elif handler["class"] == "logging_loki.LokiHandler":
            handler["tags"] = log_metadata
            # Here we want to fix up the LOKI log handler via whatever secrets
            # management technique applies.
            # Internally, we do this with a keyfile and db
        elif handler["class"] == "watchtower.CloudWatchLogHandler":
            handler["boto3_client"] = boto3.client(
                "logs",
                "us-west-2",
            )

    logging.setLogRecordFactory(make_record_factory(log_metadata,
                                                    always_pass_exc_info))

    logging.config.dictConfig(log_config)

    if send_start_log:
        logging.info("Starting")
        atexit.register(lambda: logging.info("Stopping"))

    return logging.getLogger(logger_name)


def get_queue_handler(
    name: str = "",
    queue: Queue = None,
    max_size: int = 1000,
    log_level: int = logging.INFO,
    logger: logging.Logger = None,
) -> logging.handlers.QueueHandler:
    """
    QueueHandlers are a place to aggregate logs for review internally
    in your app.  For example, a status bar might
    want to create a queue, so it can view logs and add their text
    to the status bar without messing up location
    information.

    You can create arbitrarily named queues and reference them later
    in your application.  If a handler with name
    already exists, that will be returned to you.

     :param name: [default] The name of the handler.
     The default is "default"
     :param max_size: [1000] The number of logs the queue can contain.
     If full, insertion of logs will block.
     :param log_level: [logging.INFO] The log level (INFO, WARNING, ERROR, etc)
     :param logger: [root] A logger on which to attach the handler.
     :param queue: [None] A queue object to pass to a new QueueHandler.
      One will be created if queue=None
     :returns handler:  The QueueHandler you requested
    """

    name = name or "default"
    if name in get_queue_handler.queue_handlers:
        return get_queue_handler.queue_handlers[name]

    queue = queue or Queue(maxsize=max_size)
    handler = logging.handlers.QueueHandler(queue)
    handler.setLevel(log_level)

    logger = logger or logging.getLogger()
    logger.addHandler(handler)
    get_queue_handler.queue_handlers[name] = handler

    return handler


get_queue_handler.q = Queue()
get_queue_handler.queue_handlers = {}
