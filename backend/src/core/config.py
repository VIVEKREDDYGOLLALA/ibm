# src/core/config.py
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Get the project root directory (where .env should be)
project_root = Path(__file__).parent.parent.parent  # Go up from src/core/ to project root
env_path = project_root / ".env"

# Load .env file with explicit path
load_dotenv(dotenv_path=env_path, verbose=True)

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Jira Configuration
    JIRA_URL: str = ""
    JIRA_EMAIL: str = ""
    JIRA_API_TOKEN: str = ""
    
    # GitHub Configuration
    GITHUB_TOKEN: str = ""
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    
    # IBM Granite Configuration
    IBM_GRANITE_API_KEY: str = ""
    IBM_GRANITE_ENDPOINT: str = ""
    IBM_PROJECT_ID: str = ""
    
    # Application Configuration
    PDF_OUTPUT_DIR: str = "./output/pdfs"
    TEMP_DIR: str = "./temp"
    
    # API Configuration
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    class Config:
        env_file = str(env_path)
        case_sensitive = True
        env_file_encoding = 'utf-8'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Manually load from environment if not set
        if not self.JIRA_URL:
            self.JIRA_URL = os.getenv("JIRA_URL", "")
        if not self.JIRA_EMAIL:
            self.JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
        if not self.JIRA_API_TOKEN:
            self.JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
        if not self.GITHUB_TOKEN:
            self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
        if not self.IBM_GRANITE_API_KEY:
            self.IBM_GRANITE_API_KEY = os.getenv("IBM_GRANITE_API_KEY", "")
        if not self.IBM_GRANITE_ENDPOINT:
            self.IBM_GRANITE_ENDPOINT = os.getenv("IBM_GRANITE_ENDPOINT", "")
        if not self.IBM_PROJECT_ID:
            self.IBM_PROJECT_ID = os.getenv("IBM_PROJECT_ID", "")

    def validate_jira_config(self) -> bool:
        """Validate Jira configuration"""
        result = bool(self.JIRA_URL and self.JIRA_EMAIL and self.JIRA_API_TOKEN)
        if not result:
            print(f"Jira config validation failed:")
            print(f"  JIRA_URL: {'✓' if self.JIRA_URL else '✗'} ({self.JIRA_URL})")
            print(f"  JIRA_EMAIL: {'✓' if self.JIRA_EMAIL else '✗'} ({self.JIRA_EMAIL})")
            print(f"  JIRA_API_TOKEN: {'✓' if self.JIRA_API_TOKEN else '✗'} ({'Set' if self.JIRA_API_TOKEN else 'Not set'})")
        return result
    
    def validate_github_config(self) -> bool:
        """Validate GitHub configuration"""
        return bool(self.GITHUB_TOKEN)
    
    def validate_granite_config(self) -> bool:
        """Validate IBM Granite configuration"""
        result = bool(self.IBM_GRANITE_API_KEY)
        if not result:
            print(f"IBM Granite config validation failed:")
            print(f"  IBM_GRANITE_API_KEY: {'✓' if self.IBM_GRANITE_API_KEY else '✗'} ({'Set' if self.IBM_GRANITE_API_KEY else 'Not set'})")
            print(f"  IBM_PROJECT_ID: {'✓' if self.IBM_PROJECT_ID else '✗'} ({'Set' if self.IBM_PROJECT_ID else 'Not set'})")
        return result

# Create global settings instance
settings = Settings()

# Debug print on import
if __name__ == "__main__":
    print(f"Environment file path: {env_path}")
    print(f"Environment file exists: {env_path.exists()}")
    print(f"JIRA_URL: {settings.JIRA_URL}")
    print(f"JIRA_EMAIL: {settings.JIRA_EMAIL}")
    print(f"JIRA_API_TOKEN: {'Set' if settings.JIRA_API_TOKEN else 'Not set'}")
    print(f"IBM_GRANITE_API_KEY: {'Set' if settings.IBM_GRANITE_API_KEY else 'Not set'}")
    print(f"IBM_PROJECT_ID: {'Set' if settings.IBM_PROJECT_ID else 'Not set'}")
    print(f"Jira config valid: {settings.validate_jira_config()}")
    print(f"Granite config valid: {settings.validate_granite_config()}")