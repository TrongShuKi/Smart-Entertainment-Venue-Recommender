from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Gemini AI
    GEMINI_API_KEY: str = ""

    # OpenWeatherMap
    WEATHER_API_KEY: str = ""
    WEATHER_API_TIMEOUT: float = 10.0

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # App
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
