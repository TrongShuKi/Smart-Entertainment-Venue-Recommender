import httpx
import redis.asyncio as redis
import logging
import json

from pydantic import BaseModel
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)

class WeatherResponse(BaseModel):
    weatherCondition: str
    temperature: float
    rainProbability: float


redis_pool = redis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)
redis_client = redis.Redis(connection_pool=redis_pool)

async def get_weather_cache(key: str) -> dict | None:
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.warning(f"Redis cache read error, cache skipped: {e}")
        return None


async def _set_weather_cache(key: str, data: dict, ttl: int = 3600):
    try:
        await redis_client.setex(key, ttl, json.dumps(data))
    except Exception as e:
        logger.warning(f"Redis cache write error: {e}")

#####

async def get_coordinates(location: str) -> tuple[float, float]:
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": location,
        "limit": 1,
        "appid": settings.WEATHER_API_KEY
    }
    
    async with httpx.AsyncClient(timeout=settings.WEATHER_API_TIMEOUT) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            raise ValueError(f"No coordinates found for the location: {location}")
            
        return data[0]["lat"], data[0]["lon"]

async def get_weather_by_coords(lat: float, lon: float, time: str) -> dict:
    target_time = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")

    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": settings.WEATHER_API_KEY,
        "units": "metric"
    }
    
    async with httpx.AsyncClient(timeout=settings.WEATHER_API_TIMEOUT) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        forecasts = data["list"]

        closest = min(
            forecasts,
            key=lambda x : abs(
                datetime.strptime(x["dt_txt"], "%Y-%m-%d %H:%M:%S") - target_time
            ),
        )

        weather_condition = closest["weather"][0]["main"].upper()
        temperature = closest["main"]["temp"]
        rain_probability = closest.get("pop", 0)

        return {
            "weatherCondition": weather_condition,
            "temperature": temperature,
            "rainProbability": rain_probability
        }


##########

async def get_weather_data(location: str, time: str) -> WeatherResponse:
    cache_key = f"weather:owm:{location}:{time}"
    
    cached_data = await get_weather_cache(cache_key)
    if cached_data:
        logger.info(f"Cache Hit! Returns Redis data for: {cache_key}")
        return WeatherResponse(**cached_data)
        
    logger.info(f"Cache Miss! Start making API calls to the location: {location}")
    
    try:
        lat, lon = await get_coordinates(location)
        raw_data = await get_weather_by_coords(lat, lon, time)
        
    except ValueError as ve:
        raise Exception(str(ve))
    except Exception as e:
        logger.error(f"Error when calling the OpenWeatherMap API: {e}")
        raise Exception("Weather data cannot be retrieved from third-party servers at this time")
    

    await _set_weather_cache(cache_key, raw_data, ttl=3600)
    
    return WeatherResponse(**raw_data)


