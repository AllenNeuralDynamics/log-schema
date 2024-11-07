import logging

from aind_log_utils import setup_logging

from module_1 import module_1_func
from tests.test_application.module_2 import module_2_func

logger_before = logging.getLogger("wont_work")

logger_named = logging.getLogger("test_application.before")

logger = setup_logging("test_application")

logger_named_after = logging.getLogger("test_application.after")

logger_after = logging.getLogger("will_work")


def main():
    logger.info("Info message")
    logger.error("Test error")

    logging.getLogger("test_application").info("base")

    logger_before.info("bad")
    logger_after.info("good")
    logger_named.info("named")
    logger_named_after.info("named after")

    module_1_func()
    module_2_func()

    # Expect:
    #


# 11/07/2024 02:44:52 PM, Info message
# 11/07/2024 02:44:52 PM, Test error
# 11/07/2024 02:44:52 PM, Info from module_1
# 11/07/2024 02:44:52 PM, Info from module_2


if __name__ == "__main__":
    main()
