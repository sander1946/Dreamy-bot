import discord
from loguru import logger as lg
import sys
from typing import Union

# Class to log messages
class Logger(object):
    _instance: Union["Logger", bool] = False
    
    def __init__(self):
        """Create a new instance of the Logger class."""
        # there can be only one instance of the logger, so there is no need to do anything here
        pass
    
    def __new__(cls, *args, **kwargs) -> "Logger":
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls, *args, **kwargs)
        return cls._instance
        
    # Function to setup the logger
    def setup_logger(self):
        """The function to setup the logger with different handlers."""
        log_format = "<fg #706d6a><b>{time:YYYY-MM-DD HH:mm:ss}</b></fg #706d6a> <level>{level: <8}</level> <fg #996c92>{file}.{function}:{line}</fg #996c92> <level>{message}</level> | <level>{extra}</level>"
        lg.remove(0)
        lg.add(sys.stderr, level="SUCCESS", format=log_format, colorize=True)
        lg.add("/dreamy-data/logs/debug.log", level="DEBUG", format=log_format, retention="4 days")
        lg.add("/dreamy-data/logs/info.log", level="INFO", format=log_format, retention="7 days")
        lg.add("/dreamy-data/logs/error.log", level="ERROR", format=log_format, retention="14 days")
        lg.level("PRINT", no=9999, color="<green><b>")


    # Function to log messages
    def log(self, level: str, message: str, extra: dict[str: any] = None, depth=1) -> None:
        """The function to log messages with different levels.

        Args:
            level (str): This can be one of the following: DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL, PRINT
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        # if extra:
        match level:
            case "DEBUG":
                return lg.opt(depth=depth).debug(message, extra)
            case "INFO":
                return lg.opt(depth=depth).info(message, extra)
            case "SUCCESS":
                return lg.opt(depth=depth).success(message, extra)
            case "WARNING":
                return lg.opt(depth=depth).warning(message, extra)
            case "ERROR":
                return lg.opt(depth=depth).error(message, extra)
            case "CRITICAL":
                return lg.opt(depth=depth).critical(message, extra)
            case "PRINT":
                return lg.opt(depth=depth).log("PRINT", message, extra)
            case _:
                return lg.opt(depth=depth).log("PRINT", message, extra)
    
    
    def command(self, interaction: discord.Interaction, extra: dict[str: any] = None) -> None:
        """The function to log command messages.

        Args:
            message (discord.Message): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        if not extra:
            extra = {}
        extra["user_id"] =  interaction.user.id
        extra["username"] = interaction.user.name
        extra["display_name"] = interaction.user.display_name
        extra["channel_id"] = interaction.channel.id
        extra["channel_name"] = interaction.channel.name
        extra["guild_id"] = interaction.guild.id
        extra["guild_name"] = interaction.guild.name
        
        self.log("DEBUG", f"Command executed by {extra['display_name']} in {extra['guild_name']}#{extra['channel_name']}", extra, depth=2)

    def debug(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log debug messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("DEBUG", message, extra, depth=2)
    
    def info(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log info messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("INFO", message, extra, depth=2)
    
    def success(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log success messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("SUCCESS", message, extra, depth=2)
    
    def warning(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log warning messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("WARNING", message, extra, depth=2)
    
    def error(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log error messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("ERROR", message, extra, depth=2)
    
    def critical(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log critical messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("CRITICAL", message, extra, depth=2)
        
    def print(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log print messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("PRINT", message, extra, depth=2)
        
    def exception(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log exception messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("ERROR", message, extra, depth=2)
    
    def traceback(self, message: str, extra: dict[str: any] = None) -> None:
        """The function to log traceback messages.

        Args:
            message (str): The message to log
            extra (dict, optional): Optional extra dict with whatever contect in needed.
        """
        self.log("ERROR", message, extra, depth=2)

# Class to log messages
logger = Logger()
logger.setup_logger()