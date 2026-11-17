import logging

import pytest


@pytest.fixture(autouse=True)
def reset_root_logger():
    root = logging.getLogger()
    handlers, filters, level = list(root.handlers), list(root.filters), root.level
    yield
    for handler in list(root.handlers):
        if handler not in handlers:
            root.removeHandler(handler)
            handler.close()
    root.filters[:] = filters
    root.setLevel(level)
