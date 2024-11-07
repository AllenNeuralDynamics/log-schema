from aind_log_utils import setup_logging

logger = setup_logging("test_application")

from module_1 import module_1_func
from tests.test_application.module_2 import module_2_func

# don't put setup_logging here otherwise module_1 won't log


def main():
    logger.info("Info message")
    logger.error("Test error")
    print(logger.name)

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
