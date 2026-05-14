from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.services.weather_service import get_weather_data, WEATHER_CONDITION_VI

router = APIRouter()

@router.get("/current")
async def get_weather(lat: float, lon: float):
    try:
        location_name = f"{lat},{lon}"   
        current_time  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        w = await get_weather_data(location_name, current_time)

        return {
            "condition":        w.weatherCondition,
            "condition_vi":     WEATHER_CONDITION_VI.get(w.weatherCondition, ""),
            "temperature":      w.temperature,
            "rain_probability": w.rainProbability,
            "source":           "api",
        }

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Không lấy được thời tiết: {str(e)}")