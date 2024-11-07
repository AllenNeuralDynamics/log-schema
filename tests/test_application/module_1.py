import logging

logger = logging.getLogger("aind_logger.mod1")


def module_1_func():
    logger.info("Info from module_1")
    print(logger.name)
    # print(__name__)
