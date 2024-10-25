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

log_record_factory = logging.getLogRecordFactory()
q = Queue()
queue_handlers = {}

if not os.getenv("AIND_LOG_UTILS_DEV_MODE", False):
    logging.raiseExceptions = False


def project_path(project_name: str) -> pathlib.Path:
    if path := os.getenv(f'{project_name}_path', None) is None:
        if 'windows' in platform.uname().system.lower():
            path = f'c:/ProgramData/AIND/{project_name}'
        else:
            path = os.path.expandvars(f'~/.config/AIND/{project_name}')
    return pathlib.Path(path)


def load_logging_config(project_name: str) -> dict:
    log_config_file = project_path(project_name) / f'{project_name}.yml'
    if filename := os.getenv(f'{project_name}_logfile', None):
        log_config = yaml.safe_load(open(filename, 'r'))
    elif os.path.exists(log_config_file):

        log_config = yaml.safe_load(open(log_config_file, 'r'))
    else:
        log_config = yaml.safe_load(resources.read_text("aind_log_utils", "default_logging.yml"))
        try:
            os.makedirs(project_path(project_name), exist_ok=True)
            yaml.dump(log_config, open(log_config_file, 'w'))
        except IOError as e:
            print(f"Could not write logging configuration to {log_config_file}: {e}")
        else:
            print(f"Default logging configuration to {log_config_file}")

    return log_config


def setup_logging(project_name: str, send_start_log: bool = True, always_pass_exc_info=False):
    """
    Logging setup consists of
      1.  applying the logging configuration to the Python logging module
      2.  injecting additional data into the log records via the log factory
      3.  sending a start log and registering to send a stop log
    :param project_name: The name of the configuration, usually project name, you want to find
    :param send_start_log: Whether to send a log to the webserver (not desirable for libraries) [default = True]
    :param version: The version of the software to record in the log record
    :param always_pass_exc_info: whether to always check for exc_info
    """

    frame = inspect.currentframe().f_back
    module = inspect.getmodule(frame)
    calling_package = module.__package__

    log_config = load_logging_config(project_name)

    # Find file handlers and ensure the path exists to write the log file
    # Also, the default file handler "default_file_handler" is renamed to have the project name in it.
    handlers = log_config["handlers"]
    if "default_file_handler" in handlers:
        handlers["default_file_handler"]["filename"] = handlers["default_file_handler"]["filename"].format(
            proj_name=project_name)

    for handler in handlers:
        # Configure all file handlers
        if "FileHandler" in handlers[handler]["class"] and "filename" in handlers[handler]:
            os.makedirs(os.path.dirname(handlers[handler]["filename"]), exist_ok=True)

    # Here we want to fix up the LOKI log handler via whatever secrets management technique applies.
    # Internally, we do this with a keyfile and db

    # Identifies all logs as existing between the launch and tear down of the application
    session_parts = [str(datetime.datetime.now()), platform.node(), str(os.getpid())]
    log_session = md5((''.join(session_parts)).encode("utf-8")).hexdigest()[:7]

    hostname = platform.uname().node
    comp_id = os.getenv("aibs_comp_id", "undefined")

    # We could consider better how to obtain the version of the calling package
    try:
        version = importlib.metadata.version(calling_package)
    except:
        version = 'N/A'  # Probably a 1 off script that's not installed so it likely won't have a version

    user_name = getpass.getuser()

    def record_factory(*args, **kwargs):
        record = log_record_factory(*args, **kwargs)
        if not record.exc_info and always_pass_exc_info:
            record.exc_info = sys.exc_info()
            record.exc_text = traceback.format_exc()
        record.hostname = hostname
        record.comp_id = comp_id
        record.version = version
        record.project = project_name
        record.log_session = log_session
        record.user_name = user_name
        # we need to add these as tags to loki

        if type(record.msg) is str:
            record.msg = record.msg if record.msg and record.msg[-1] == ',' else record.msg + ','
        if isinstance(record.msg, dict):
            record.msg = ", ".join([str(item) for keyval in record.msg.items() for item in keyval])
        return record

    logging.setLogRecordFactory(record_factory)

    """ 
    Uses dictionary to configure the logging module. Dictionary pulls info config from:
            1. defaults: defined above (caches locally after running once) OR pulled from local config file
            2. logging_v2" from a custom project [Optional]
    """

    logging.config.dictConfig(log_config)

    if send_start_log:
        logging.info("Starting")
        atexit.register(lambda: logging.info("Stopping"))

    return logging.getLogger('aind_logger')


def get_queue_handler(name: str = "", queue: Queue = None, max_size: int = 1000, log_level: int = logging.INFO,
                      logger: logging.Logger = None) -> logging.handlers.QueueHandler:
    """
       QueueHandlers are a place to aggregate logs for review internally in your app.  For example, a status bar might
       want to create a queue, so it can view logs and add their text to the status bar without messing up location
       information.

       You can create arbitrarily named queues and reference them later in your application.  If a handler with name
       already exists, that will be returned to you.

        :param name: [default] The name of the handler.  The default is "default"
        :param max_size: [1000] The number of logs the queue can contain.  If full, insertion of logs will block.
        :param log_level: [logging.INFO] The log level (INFO, WARNING, ERROR, etc)
        :param logger: [root] A logger on which to attach the handler.
        :param queue: [None] A queue object to pass to a new QueueHandler.  One will be created if queue=None
        :returns handler:  The QueueHandler you requested
    """

    name = name or "default"
    if name in queue_handlers:
        return queue_handlers[name]

    queue = queue or Queue(maxsize=max_size)
    handler = logging.handlers.QueueHandler(queue)
    handler.setLevel(log_level)

    logger = logger or logging.getLogger()
    logger.addHandler(handler)
    queue_handlers[name] = handler

    return handler
