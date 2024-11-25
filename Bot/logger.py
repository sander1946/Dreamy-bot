from loguru import logger
import sys

# Function to setup the logger
def setup_logger():
    """The function to setup the logger with different handlers."""
    log_format = "<fg #706d6a><b>{time:YYYY-MM-DD HH:mm:ss}</b></fg #706d6a> <level>{level: <8}</level> <fg #996c92>{file}.{function}:{line}</fg #996c92> <level>{message}</level> | <level>{extra}</level>"
    logger.remove(0)
    logger.add(sys.stderr, level="DEBUG", format=log_format, colorize=True)
    logger.add("logs/debug.log", level="DEBUG", retention="4 days")
    logger.add("logs/info.log", level="INFO", retention="7 days")
    logger.add("logs/error.log", level="ERROR", retention="14 days")
    
    logger.level("PRINT", no=9999, color="<green><b>", icon="🐍")


# Function to log messages
def log(level: str, message: str, extra: dict[str: any] = None) -> None:
    """The function to log messages with different levels.

    Args:
        level (str): This can be one of the following: DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL, PRINT
        message (str): The message to log
        extra (dict, optional): Optional extra dict with whatever contect in needed.
    """
    if extra:
        match level:
            case "DEBUG":
                return logger.debug(message, extra=extra)
            case "INFO":
                return logger.info(message, extra=extra)
            case "SUCCESS":
                return logger.success(message, extra=extra)
            case "WARNING":
                return logger.warning(message, extra=extra)
            case "ERROR":
                return logger.error(message, extra=extra)
            case "CRITICAL":
                return logger.critical(message, extra=extra)
            case "PRINT":
                return logger.log("PRINT", message, extra=extra)
            case _:
                return logger.log("PRINT", message, extra=extra)
    else:
        match level:
            case "DEBUG":
                return logger.debug(message)
            case "INFO":
                return logger.info(message)
            case "SUCCESS":
                return logger.success(message)
            case "WARNING":
                return logger.warning(message)
            case "ERROR":
                return logger.error(message)
            case "CRITICAL":
                return logger.critical(message)
            case "PRINT":
                return logger.log("PRINT", message)
            case _:
                return logger.log("PRINT", message)
