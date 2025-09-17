"""
Logging configuration for Aviation MAS-A2A system
"""
import sys
from loguru import logger
from .config import config


def setup_logging():
    """Configure logging for the aviation system"""
    
    # Remove default handler
    logger.remove()
    
    # Configure format based on config
    if config.log_format == "json":
        log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
    else:
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=config.log_level,
        colorize=True if config.log_format != "json" else False,
        backtrace=True,
        diagnose=True,
    )
    
    # Add file handler for errors
    logger.add(
        "logs/aviation-mas-a2a.log",
        format=log_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )
    
    logger.info("Logging configured for Aviation MAS-A2A system")
    return logger