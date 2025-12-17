from loguru import logger

import aind_log_utils
import aind_log_utils.handlers as log_handlers
import aind_log_utils.models as log_models


def main():
    print("EXAMPLE: BASIC DEFAULT ============================================")

    model = log_models.DefaultLogFields()
    aind_log_utils.setup_logger(
        handlers=[log_handlers.FILE_HANDLER, log_handlers.CONSOLE_HANDLER],
        model=model,
    )
    logger.info("Test log")

    print("EXAMPLE: BASIC FORAGING ===========================================")

    # Set log fields with a model
    model = log_models.ForagingLogFields(scientist="Jimmy McExperiment")
    aind_log_utils.setup_logger(
        handlers=[log_handlers.CONSOLE_HANDLER],
        model=model,
    )
    logger.info("The subject has done what I designed it to do")

    print("EXAMPLE: EXTRA FROM SETUP_LOGGER ==================================")

    # Set log fields by passing in extra dictionary
    model = log_models.DefaultLogFields()
    aind_log_utils.setup_logger(
        handlers=[log_handlers.FILE_HANDLER, log_handlers.CONSOLE_HANDLER],
        model=model,
        extra={"instance": "8", "random": "beepboop"},
    )
    logger.info("Test log")

    print("EXAMPLE: MODEL OVERRIDE ===========================================")

    # Set comp_id by updating the model and passing it to the log
    model.comp_id = "8"
    logger.info("Test log", model=model)

    print("EXAMPLE: EXTRA OVERRIDE ===========================================")

    # Set comp_id directly as a parameter
    logger.info("Test log", comp_id="8")

    print("EXAMPLE: OVERRIDE PRECEDENCES =====================================")

    # 4) Lowest precedence for field override (default fields in model defined in setup_logger)
    model = log_models.DefaultLogFields(comp_id="4")
    aind_log_utils.setup_logger(
        handlers=[log_handlers.FILE_HANDLER, log_handlers.CONSOLE_HANDLER],
        model=model,
    )
    logger.info("4")

    # 3) 3rd precedence for field override (model defined in individual log record)
    model.comp_id = "3"
    logger.info("3", model=model)

    # 2) 2nd precedence for field override (extras defined in setup_logger)
    aind_log_utils.setup_logger(
        handlers=[log_handlers.FILE_HANDLER, log_handlers.CONSOLE_HANDLER],
        model=model,
        extra={"comp_id": "2"},
    )
    logger.info("2", model=model)

    # 1) Highest precedence for field override (extras defined in individual log record)
    logger.info("1", model=model, comp_id="1")

    print("EXAMPLE: MIX N MATCH ==============================================")

    aind_log_utils.setup_logger(
        handlers=[log_handlers.FILE_HANDLER, log_handlers.CONSOLE_HANDLER],
        model=model,
        extra={"comp_id": "2"},
    )

    # All parameters given gets added into log_record["extra"].
    logger.info("1", model=model, more="extras", what="ever", you="like")


if __name__ == "__main__":
    main()
