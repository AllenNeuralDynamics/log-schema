from aind_log_utils import log

subject_id = "999999"
session_id = f"{subject_id}-110824"

logger = log.setup_logging(
    "codeocean-test",
    subject_id=subject_id,
    session_id=session_id,
)

message_template = "This is a test {} message"
logger.debug(message_template.format("debug"))
logger.info(message_template.format("info"))
logger.warning(message_template.format("warning"))
logger.error(message_template.format("error"))
