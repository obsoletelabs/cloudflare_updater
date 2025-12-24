"""Setup a logger for the project"""

import logging
import sys

from colorlog import ColoredFormatter


def setup_logger(logging_level: str, debug_logger_format: bool) -> logging.Logger:
    """Creates and returns the logger"""
    if logging_level == "DEBUG":
        log_level = logging.DEBUG
    elif logging_level == "WARNING":
        log_level = logging.WARNING
    elif logging_level == "ERROR":
        log_level = logging.ERROR
    elif logging_level == "CRITICAL":
        log_level = logging.CRITICAL
    else:
        log_level = logging.INFO
        logging_level = "INFO"

    # logger setup

    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s]%(reset)s %(message_log_color)s%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "light_black",  # color for the prefix
            "INFO": "reset",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
        secondary_log_colors={
            "message": {
                "DEBUG": "light_black",  # <-- gray message text
                "INFO": "reset",
                "WARNING": "yellow",
                "ERROR": "yellow",
                "CRITICAL": "yellow",
            }
        },
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logging.basicConfig(level=logging.DEBUG, handlers=[handler])

    logger = logging.getLogger(__name__)

    # for testing formats
    if debug_logger_format:
        logger.debug("debug")
        logger.info("info")
        logger.warning("warning")
        logger.error("error")
        logger.critical("critical")

    # finish up
    logger.info("Logging level set to %s", logging_level)  # log the logging level as critical to ensure logged.
    logger.setLevel(log_level)

    logger.info("Service starting up...")  # log startup
    return logger
