import sys
from logging import FileHandler


DEFAULT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<bold>{message}</bold> | "
    "{extra}"
)


FILE_HANDLER = {
    "sink": FileHandler("app.log"),
    "format": DEFAULT_FORMAT,
}


CONSOLE_HANDLER = {
    "sink": sys.stdout,
    "format": DEFAULT_FORMAT,
}
