from fastapi import APIRouter

router = APIRouter()

@router.get("/current")
async def get_weather(lat: float, lon: float):
    # SAU NÀY NHÓM WEATHER SẼ CODE GỌI API THỜI TIẾT THẬT Ở ĐÂY
    return {
        "condition": "RAIN",
        "temperature": "COOL",
        "message": f"Dữ liệu thời tiết giả lập tại tọa độ {lat}, {lon}"
    }