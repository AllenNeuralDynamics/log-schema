import logging
from aind_log_utils import log


log.setup_logging(
    "test_docs_aind-log-utils",  # project_name
)

logger = logging.getLogger("__name__")

logger.info("This is a test message for watchtower integration.")
