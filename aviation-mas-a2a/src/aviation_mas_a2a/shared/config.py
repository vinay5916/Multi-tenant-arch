"""
Shared configuration for Aviation MAS-A2A system
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Config(BaseSettings):
    """Global configuration for the aviation system"""
    
    # API Keys and Authentication
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    google_cloud_project: str = Field(default="aviation-mas-a2a", env="GOOGLE_CLOUD_PROJECT")
    
    # LLM Configuration
    default_model: str = Field(default="openai/gpt-4o-mini", env="DEFAULT_MODEL")
    temperature: float = Field(default=0.1, env="MODEL_TEMPERATURE")
    max_tokens: int = Field(default=2000, env="MAX_TOKENS")
    
    # LiteLLM Configuration
    litellm_model: str = Field(default="gpt-3.5-turbo", env="LITELLM_MODEL")
    litellm_api_key: Optional[str] = Field(default=None, env="LITELLM_API_KEY")
    litellm_base_url: Optional[str] = Field(default=None, env="LITELLM_BASE_URL")
    
    # Server Configuration
    server_host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    server_port: int = Field(default=8000, env="SERVER_PORT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # MCP Server Configuration
    mcp_host: str = Field(default="localhost", env="MCP_HOST")
    mcp_base_port: int = Field(default=9000, env="MCP_BASE_PORT")
    
    # Aviation Business Configuration
    aviation_departments: list[str] = Field(default=[
        "Flight Operations", "Maintenance", "Ground Services", "Air Traffic Control",
        "Safety & Security", "Customer Service", "Cargo Operations", "Engineering",
        "Quality Assurance", "Training", "Human Resources", "Finance"
    ])
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global config instance
config = Config()