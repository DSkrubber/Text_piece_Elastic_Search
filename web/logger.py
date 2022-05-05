import logging
import sys

_log_format = (
    "%(asctime)s - [%(levelname)s] - %(name)s - "
    "(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
)
_file_handler = logging.FileHandler("./application.log")
_stream_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(
    format=_log_format, level="INFO", handlers=(_file_handler, _stream_handler)
)


def get_logger(name: str) -> logging.Logger:
    """Returns logger with specified name.

    :param name: modules name that will be used in %(name)s of log_format.
    :return: logger instance.
    """
    logger = logging.getLogger(name)
    return logger
