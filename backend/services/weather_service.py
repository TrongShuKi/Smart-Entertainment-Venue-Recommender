"""
weather_service.py
==================
Cung cấp dữ liệu thời tiết từ OpenWeatherMap API.
Cache bằng JSON file thay thế Redis (không cần cài thêm gì).

Exports dùng bởi chat_router:
    - WEATHER_CONDITION_VI  : dict map condition → tiếng Việt
    - parse_weather_from_tags() : phát hiện thời tiết từ NLP tags
    - get_weather_data()    : gọi OWM API, trả WeatherResponse
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import httpx
from pydantic import BaseModel

from backend.core.config import settings

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# MAPS — dùng bởi chat_router (PHẢI export đủ)
# ══════════════════════════════════════════════════════════════════════════════

# Từ khoá thời tiết người dùng hay dùng → condition chuẩn OWM
WEATHER_TAG_MAP: dict[str, str] = {
    "mưa":        "RAIN",   "trời mưa":  "RAIN",   "mưa lớn":   "RAIN",
    "mưa nhỏ":   "RAIN",   "mưa phùn":  "RAIN",
    "bão":        "STORM",  "dông bão":  "STORM",  "dông":      "STORM",
    "nắng":       "CLEAR",  "trời nắng": "CLEAR",  "nắng đẹp":  "CLEAR",
    "nắng gắt":   "CLEAR",
    "mây":        "CLOUDS", "u ám":      "CLOUDS", "nhiều mây": "CLOUDS",
}

# Condition code → tên tiếng Việt (dùng khi build response / context string)
WEATHER_CONDITION_VI: dict[str, str] = {
    "RAIN":    "trời mưa",
    "STORM":   "có bão",
    "DRIZZLE": "mưa nhỏ",
    "CLEAR":   "nắng đẹp",
    "CLOUDS":  "nhiều mây",
    "MIST":    "sương mù",
    "SNOW":    "lạnh",
}


# ══════════════════════════════════════════════════════════════════════════════
# SCHEMA
# ══════════════════════════════════════════════════════════════════════════════

class WeatherResponse(BaseModel):
    weatherCondition: str
    temperature: float
    rainProbability: float


# ══════════════════════════════════════════════════════════════════════════════
# CACHE JSON FILE — thay thế Redis, không cần cài thêm gì
# ══════════════════════════════════════════════════════════════════════════════

_CACHE_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "weather_cache.json"
_CACHE_TTL  = settings.WEATHER_CACHE_TTL   # giây, mặc định 1800 (30 phút)


def _load_cache() -> dict:
    """Đọc toàn bộ cache từ file JSON. Trả {} nếu file chưa tồn tại."""
    try:
        if _CACHE_FILE.exists():
            return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"[Cache] Lỗi đọc cache file: {e}")
    return {}


def _save_cache(cache: dict) -> None:
    """Ghi cache xuống file JSON."""
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.warning(f"[Cache] Lỗi ghi cache file: {e}")


def _get_cached(key: str) -> Optional[dict]:
    """Lấy 1 entry từ cache. Trả None nếu không tồn tại hoặc đã hết TTL."""
    cache = _load_cache()
    entry = cache.get(key)
    if not entry:
        return None
    if time.time() - entry.get("ts", 0) > _CACHE_TTL:
        logger.info(f"[Cache] Hết hạn: {key}")
        return None
    return entry.get("data")


def _set_cached(key: str, data: dict) -> None:
    """Lưu 1 entry vào cache kèm timestamp."""
    cache = _load_cache()
    cache[key] = {"ts": time.time(), "data": data}
    _save_cache(cache)


# ══════════════════════════════════════════════════════════════════════════════
# HELPER — phát hiện thời tiết từ NLP tags (không tốn API call)
# ══════════════════════════════════════════════════════════════════════════════

def parse_weather_from_tags(tags: List[str]) -> Optional[str]:
    """
    Duyệt NLP tags tìm từ khoá thời tiết.
    VD: ["chill", "mưa", "cặp đôi"] → "RAIN"
    Trả None nếu không có tag thời tiết nào.
    """
    for tag in tags:
        condition = WEATHER_TAG_MAP.get(tag.lower().strip())
        if condition:
            return condition
    return None


# ══════════════════════════════════════════════════════════════════════════════
# OWM API CALLS
# ══════════════════════════════════════════════════════════════════════════════

async def get_coordinates(location: str) -> tuple[float, float]:
    """Geocoding: tên địa điểm → (lat, lon) qua OWM Geo API."""
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {"q": location, "limit": 1, "appid": settings.WEATHER_API_KEY}

    async with httpx.AsyncClient(timeout=settings.WEATHER_API_TIMEOUT) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    if not data:
        raise ValueError(f"Không tìm thấy tọa độ cho: {location}")

    return data[0]["lat"], data[0]["lon"]


async def get_weather_by_coords(lat: float, lon: float, target_time: str) -> dict:
    """Lấy dự báo thời tiết gần nhất với target_time từ OWM Forecast API."""
    dt_target = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat, "lon": lon,
        "appid": settings.WEATHER_API_KEY,
        "units": "metric",
    }

    async with httpx.AsyncClient(timeout=settings.WEATHER_API_TIMEOUT) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    closest = min(
        data["list"],
        key=lambda x: abs(
            datetime.strptime(x["dt_txt"], "%Y-%m-%d %H:%M:%S") - dt_target
        ),
    )

    return {
        "weatherCondition": closest["weather"][0]["main"].upper(),
        "temperature":      closest["main"]["temp"],
        "rainProbability":  closest.get("pop", 0),
    }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY — được gọi bởi chat_router
# ══════════════════════════════════════════════════════════════════════════════

async def get_weather_data(location: str, target_time: str) -> WeatherResponse:
    """
    Lấy thông tin thời tiết cho location tại target_time.
    Thử cache JSON trước, nếu miss mới gọi OWM API.

    Args:
        location    : tên khu vực, VD "Ho Chi Minh City", "Quận 1"
        target_time : chuỗi "%Y-%m-%d %H:%M:%S"

    Returns:
        WeatherResponse(weatherCondition, temperature, rainProbability)

    Raises:
        Exception nếu API lỗi (chat_router đã có fallback xử lý).
    """
    cache_key = f"{location}|{target_time}"

    # ── Cache hit ────────────────────────────────────────────────────────────
    cached = _get_cached(cache_key)
    if cached:
        logger.info(f"[Weather] Cache hit: {cache_key}")
        return WeatherResponse(**cached)

    logger.info(f"[Weather] Cache miss → gọi OWM API: {location}")

    # ── Gọi API ──────────────────────────────────────────────────────────────
    try:
        t0 = time.time()
        lat, lon = await get_coordinates(location)
        raw_data = await get_weather_by_coords(lat, lon, target_time)
        logger.info(f"[Weather] API xong trong {time.time() - t0:.2f}s")

    except ValueError as ve:
        raise Exception(str(ve))
    except Exception as e:
        logger.error(f"[Weather] Lỗi OWM API: {e}")
        raise Exception("Không thể lấy dữ liệu thời tiết từ server lúc này.")

    # ── Lưu cache ────────────────────────────────────────────────────────────
    _set_cached(cache_key, raw_data)

    return WeatherResponse(**raw_data)