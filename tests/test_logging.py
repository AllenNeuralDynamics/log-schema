import logging

from aind_log_utils import setup_logging

project_name = "log_test"

logger = setup_logging(project_name=project_name)

logger.info("Test log")
logger.warning("Test warning log")
logger.error("Test error log")

pass
