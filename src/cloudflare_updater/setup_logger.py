"""Setup a logger for the project"""

import logging
import logging.handlers
import sys

# from main import init_email_context
from colorlog import ColoredFormatter


def setup_logger(
    log_level: str | int, debug_logger_format: bool, LogFilePath: str, MaxLogfileSizeBytes: int, enable_color: bool = True
) -> logging.Logger:
    """Creates and returns the logger"""

    match log_level:
        case "DEBUG":
            log_level = logging.DEBUG
        case "INFO":
            log_level = logging.INFO
        case "WARNING":
            log_level = logging.WARNING
        case "ERROR":
            log_level = logging.ERROR
        case "CRITICAL":
            log_level = logging.CRITICAL
        case int() as lvl:
            log_level = lvl

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

    file_formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s")

    handler = logging.StreamHandler(sys.stdout)
    if enable_color:
        handler.setFormatter(formatter)

    file_handler = logging.handlers.RotatingFileHandler(LogFilePath, maxBytes=(MaxLogfileSizeBytes), backupCount=7)
    file_handler.setFormatter(file_formatter)

    logging.basicConfig(level=log_level, handlers=[handler, file_handler])

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
    # init_email_context.append(f"Logging level set to {logging.getLevelName(log_level)}")
    # logger.setLevel(log_level)

    logger.info("Service starting up...")  # log startup
    return logger
