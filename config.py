import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseModel):
    # API keys
    COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")
    
    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Application
    APP_NAME: str = "Intelligent Chatbot"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    class Config:
        env_file = ".env"


settings = Settings()