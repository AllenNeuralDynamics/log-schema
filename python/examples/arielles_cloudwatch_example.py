import logging
import watchtower

from aind_log_utils import setup_logging, DefaultFormatter


# Model with fields we want to see in every log
fake_model = {"who da best": "arielle", "wow": "so many fields", "boop": "beep"}

# Setup default logging
setup_logging(model=fake_model)


def add_cloudwatch_handler(model):
    """specific helper method to add handler WITH proper formatting included"""
    handler = watchtower.CloudWatchLogHandler(
        log_stream_name="arielles-test-stream", log_group="aind/internal-logs"
    )
    handler.setFormatter(DefaultFormatter(models=fake_model))
    logging.getLogger().addHandler(handler)
