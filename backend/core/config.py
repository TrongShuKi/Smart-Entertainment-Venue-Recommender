"""
config.py
=========
Load toàn bộ biến môi trường từ file .env vào một object Settings duy nhất.
Mọi file trong dự án đều import từ đây, KHÔNG tự gọi load_dotenv() riêng lẻ.
 
Cách dùng:
    from backend.core.config import settings
    print(settings.GEMINI_API_KEY)
"""

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Gemini AI
    GEMINI_API_KEY: str = ""

    # OpenWeatherMap
    WEATHER_API_KEY: str = ""
    WEATHER_API_TIMEOUT: float = 10.0   # giây, timeout mỗi HTTP request
    WEATHER_CACHE_TTL: int = 1800       # giây = 30 phút, thời gian sống cache Re

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Rate Limiting — Giới hạn request từ phía người dùng
    RATE_LIMIT_PER_MINUTE: int = 5      # tối đa 5 lần search / phút / IP
    RATE_LIMIT_PER_DAY: int = 20        # tối đa 20 lần search / ngày / IP

    # App
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
