import atexit
import logging
import logging.config
import logging.handlers
import os
import sys
import traceback
from importlib import resources
from os import PathLike
from queue import Queue

import yaml

from settings import Settings

log_record_factory = logging.getLogRecordFactory()  # Needs to be in the global scope




def load_logging_config(filename: PathLike) -> dict:
    if not os.path.exists(filename):
        log_config = yaml.safe_load(resources.read_text("aind_log_utils", "default_logging.yml"))
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            yaml.dump(log_config, open(filename, 'w'))
        except IOError as e:
            print(f"Could not write logging configuration to {filename}: {e}")
        else:
            print(f"Default logging configuration to {filename}")
    else:
        log_config = yaml.safe_load(open(filename, 'r'))

    return log_config


def setup_logging(project_name: str, send_start_log: bool = True, always_pass_exc_info=False):
    """
    Logging setup consists of
      1.  applying the logging configuration to the Python logging module
      2.  injecting additional data into the log records via the log factory
      3.  sending a start log and registering to send a stop log
    :param project_name: The name of the configuration, usually project name, you want to find
    :param send_start_log: Whether to send a log to the webserver (not desirable for libraries) [default = True]
    :param always_pass_exc_info: whether to always check for exc_info
    """

    config = Settings(project_name=project_name)
    logging.raiseExceptions = Settings().dev_mode
    log_config = load_logging_config(config.log_config_file)

    # Find file handlers and ensure the path exists to write the log file
    # Also, the default file handler "default_file_handler" is renamed to have the project name in it.
    handlers = log_config["handlers"]
    if "default_file_handler" in handlers:
        handlers["default_file_handler"]["filename"] = handlers["default_file_handler"]["filename"].format(
            project_name=project_name)

    for handler in handlers.values():
        # Configure all file handlers
        match handler['class']:
            case "FileHandler":
                if "filename" in handler:
                    os.makedirs(os.path.dirname(handler["filename"]), exist_ok=True)

            case "logging_loki.LokiHandler":
                handler['tags'] = {
                    'project_name': project_name,
                    'comp_id': config.comp_id,
                    'log_session': config.log_session,
                    'user_name': config.user_name,
                    'version': config.version,
                    'hostname': config.hostname
                }
                # Here we want to fix up the LOKI log handler via whatever secrets management technique applies.
                # Internally, we do this with a keyfile and db

    def record_factory(*args, **kwargs):
        record = log_record_factory(*args, **kwargs)
        if not record.exc_info and always_pass_exc_info:
            record.exc_info = sys.exc_info()
            record.exc_text = traceback.format_exc()
        record.hostname = config.hostname
        record.comp_id = config.comp_id
        record.version = config.version
        record.project = config.project_name
        record.log_session = config.log_session
        record.user_name = config.user_name

        return record

    logging.setLogRecordFactory(record_factory)
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
