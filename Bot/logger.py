from loguru import logger as lg
import sys

# Class to log messages
class logger:
    def __init__(self):
        self.setup_logger()
        
    # Function to setup the logger
    def setup_logger(self):
        """The function to setup the logger with different handlers."""
        log_format = "<fg #706d6a><b>{time:YYYY-MM-DD HH:mm:ss}</b></fg #706d6a> <level>{level: <8}</level> <fg #996c92>{file}.{function}:{line}</fg #996c92> <level>{message}</level> | <level>{extra}</level>"
        lg.remove(0)
        lg.add(sys.stderr, level="DEBUG", format=log_format, colorize=True)
        lg.add("logs/debug.log", level="DEBUG", retention="4 days")
        lg.add("logs/info.log", level="INFO", retention="7 days")
        lg.add("logs/error.log", level="ERROR", retention="14 days")
        
        lg.level("PRINT", no=9999, color="<green><b>")


    # Function to log messages
    def log(self, level: str, message: str, extra: dict[str: any] = None) -> None:
        """The function to log messages with different levels.

        Args:
            level (str): This can be one of the following: DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL, PRINT
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        if extra:
            match level:
                case "DEBUG":
                    return lg.opt(depth=1).debug(message, extra=extra)
                case "INFO":
                    return lg.opt(depth=1).info(message, extra=extra)
                case "SUCCESS":
                    return lg.opt(depth=1).success(message, extra=extra)
                case "WARNING":
                    return lg.opt(depth=1).warning(message, extra=extra)
                case "ERROR":
                    return lg.opt(depth=1).error(message, extra=extra)
                case "CRITICAL":
                    return lg.opt(depth=1).critical(message, extra=extra)
                case "PRINT":
                    return lg.opt(depth=1).log("PRINT", message, extra=extra)
                case _:
                    return lg.opt(depth=1).log("PRINT", message, extra=extra)
        else:
            match level:
                case "DEBUG":
                    return lg.opt(depth=1).debug(message)
                case "INFO":
                    return lg.opt(depth=1).info(message)
                case "SUCCESS":
                    return lg.opt(depth=1).success(message)
                case "WARNING":
                    return lg.opt(depth=1).warning(message)
                case "ERROR":
                    return lg.opt(depth=1).error(message)
                case "CRITICAL":
                    return lg.opt(depth=1).critical(message)
                case "PRINT":
                    return lg.opt(depth=1).log("PRINT", message)
                case _:
                    return lg.opt(depth=1).log("PRINT", message)

    def debug(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log debug messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("DEBUG", message, extra)
    
    def info(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log info messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("INFO", message, extra)
    
    def success(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log success messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("SUCCESS", message, extra)
    
    def warning(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log warning messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("WARNING", message, extra)
    
    def error(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log error messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("ERROR", message, extra)
    
    def critical(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log critical messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("CRITICAL", message, extra)
        
    def print(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log print messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("PRINT", message, extra)
        
    def exception(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log exception messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("ERROR", message, extra)
    
    def traceback(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log traceback messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("ERROR", message, extra)