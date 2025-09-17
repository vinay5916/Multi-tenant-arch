"""
Aviation Multi-Agent System (MAS-A2A)
A comprehensive aviation operations coordination system using Google ADK, FastMCP, and LiteLLM.
"""

__version__ = "0.1.0"
__author__ = "Aviation MAS-A2A Team"
__description__ = "Aviation Multi-Agent System for HR, Meeting, and Supply Chain coordination"

from .shared.config import Config
from .shared.logging_config import setup_logging

__all__ = ["Config", "setup_logging"]