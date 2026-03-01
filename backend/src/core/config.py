# Configuration settings

from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra environment variables
    )
    
    # Database
    database_url: str = "sqlite:///:memory:"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    # Notifications
    notification_poll_interval: int = 5
    max_notification_retries: int = 3

settings = Settings()
