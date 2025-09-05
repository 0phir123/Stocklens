# File: shared/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "dev"
    log_level: str = "DEBUG"
    redis_url: str = "redis://localhost:6379/0"
    
class Config:
        env_file = ".env"
       
settings = Settings()
