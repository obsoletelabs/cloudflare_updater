"""Setup a logger for the project"""

import logging
import sys

from colorlog import ColoredFormatter


def setup_logger(log_level: int, debug_logger_format: bool, enable_color: bool = True) -> logging.Logger:
    """Creates and returns the logger"""

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
    if enable_color:
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
    logger.info("Logging level set to %s", logging.getLevelName(log_level))  # log the logging level as critical to ensure logged.
    logger.setLevel(log_level)

    logger.info("Service starting up...")  # log startup
    return logger
