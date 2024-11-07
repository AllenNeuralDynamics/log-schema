import logging
from aind_log_utils import log


log.setup_logging(
    "test_docs_aind-log-utils",  # project_name
)

logger = logging.getLogger("__name__")

logging.info("This is a test message for watchtower integration.")

logger.debug("This is a test debug message for watchtower integration.")
logger.info("This is a test info message for watchtower integration.")
logger.warning("This is a test warning message for watchtower integration.")
logger.error("This is a test error message for watchtower integration.")
