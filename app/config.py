"""
Configuration using pydantic-settings
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LiteLLM
    LITELLM_BASE_URL: str = "http://litellm.homelab.com"
    LITELLM_API_KEY: str = ""
    LITELLM_MODEL: str = "xiaomi/mimo-v2-flash"
    
    # Android TV
    ANDROID_TV_IP: str = "192.168.0.64"
    ADB_PORT: str = "5555"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:devpassword@localhost:5433/tv_controller_db"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    @property
    def DEVICE_ID(self) -> str:
        return f"{self.ANDROID_TV_IP}:{self.ADB_PORT}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
