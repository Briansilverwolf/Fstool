import logging
from .settings import LOGGING

def setup_logger(name: str, log_file: str) -> logging.Logger:
    """
    Set up a logger with the specified name and log file.

    :param name: Name of the logger.
    :param log_file: Path to the log file.
    :return: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOGGING['loggers'][name]['level'])

    # Create a file handler
    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setFormatter(logging.Formatter(LOGGING['formatters']['default']['format']))

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger