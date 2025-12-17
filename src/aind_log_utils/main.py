from loguru import logger as loguru_logger
from aind_log_utils.models.log_structure import LogStructure


def setup_logger(
    handlers: list | None = None,
    model: LogStructure | None = None,
    extra: dict | None = None,
):
    """Helper function to setup loguru logger. 
    
    This function does the following:
    - Setup patch function (function that modify log records before going to the handler). Patch function expected to be defined in each log model.
    - Setup all handlers.
    - Setup all extra fields.

    Below are the precedence rules for fields:
    1. Extra fields provided in the log call (logging.info("msg", extra="override value"))
    2. Extra fields provided in setup_logger (setup_logger(extra={"extra":"override value"}))
    3. Fields provided in the log call model (logging.info("msg", model=model_with_overrides))
    4. Fields auto-populated from the log model patch function

    Args:
        handlers: Optional Handlers to add to Loguru. Determines how to forward log data.
        model: Optional Pydantic model representing default fields for every log.
        extra: Optional dict of extra fields to add to every log record.
    """
    # Checks if model implements LogStructure protocol
    if not isinstance(model, LogStructure):
        loguru_logger.warning(
            f"Log model {model} does not follow LogStructure protocol (patch function likely missing)."
        )

    # Set initial model in extra field so initial fields get populated
    if model: 
        if extra:
            extra["model"] = model
        else: 
            extra = {"model": model}

    # Configure loguru logger
    loguru_logger.configure(
        handlers=handlers,
        patcher=model.patch if model else None,
        extra=extra,
    )
