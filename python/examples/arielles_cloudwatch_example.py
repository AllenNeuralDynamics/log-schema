import logging
import watchtower
from pythonjsonlogger import jsonlogger as log_json

from aind_log_utils import setup_logging, DefaultFormatter


# # Setup default logging
# setup_logging()


# # New handler - cloudwatch
# log_stream = "arielles-test-stream"
# handler = watchtower.CloudWatchLogHandler(
#     log_stream_name=log_stream, log_group="aind/internal-logs"
# )
# handler.setFormatter(DefaultFormatter())

# logging.getLogger().addHandler(handler)

################################################################################
#
#   Same example but with a model
#
################################################################################

# Model with fields we want to see in every log
fake_model = {
    "who da best": "arielle",
    "wow": "so many fields",
    "boop": "beep"
}

# Setup default logging
setup_logging(model=fake_model)

def add_cloudwatch_handler(model):
    """specific helper method to add handler WITH proper formatting included"""

    # New handler - cloudwatch
    log_stream = "arielles-test-stream"
    handler = watchtower.CloudWatchLogHandler(
        log_stream_name=log_stream, log_group="aind/internal-logs"
    )

    # import sys
    # handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(DefaultFormatter(models=fake_model))

    logging.getLogger().addHandler(handler)

