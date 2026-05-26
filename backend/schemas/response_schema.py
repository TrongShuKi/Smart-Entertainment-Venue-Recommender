"""
Định nghĩa cấu trúc JSON mà Backend trả về cho Frontend.
"""

from pydantic import BaseModel
from typing import List, Optional, Tuple


class Place(BaseModel):
    # ── Định danh 
    id:          str
    name:        str

    # ── Hiển thị trên thẻ địa điểm 
    category:    str   = ""             # Loại hình: Cafe, Bảo tàng, Công viên...
    tag:         str   = ""             # Tag đại diện nổi bật nhất (từ matching)
    price:       int   = 0              # Giá vé (VNĐ), 0 = miễn phí
    rating:      float = 0.0            # Điểm đánh giá gốc (1.0 – 5.0)
    image_url:   str   = ""             # URL ảnh đại diện

    # ── Bản đồ 
    latitude:    float = 0.0            # Tọa độ — Frontend dùng để đặt Marker
    longitude:   float = 0.0
    distance:    float = 0.0            # Khoảng cách từ user (km)

    # ── Nội dung AI sinh ra 
    description: str   = ""            # Mô tả ngắn 1–2 câu
    fact:        str   = ""            # Sự thật thú vị về địa điểm


class WeatherInfo(BaseModel):
    """Thông tin thời tiết đính kèm response — hiển thị context trên UI."""
    condition:        str   = ""        # "RAIN" | "CLEAR" | "CLOUDS" | "STORM"
    condition_vi:     str   = ""        # "Trời mưa" | "Nắng đẹp" ... (tiếng Việt)
    temperature:      float = 0.0       # Nhiệt độ (°C)
    rain_probability: float = 0.0       # Xác suất có mưa (0.0 – 1.0)
    source:           str   = "api"     # "api" = lấy từ API | "user" = user tự cung cấp
    location_name:    str   = ""


class SuggestionResponse(BaseModel):
    status:               str              # "success" | "fallback" | "error"
    message:              str              # Thông báo hiển thị cho người dùng
    top_places:           List[Place]      # Danh sách Top 3 địa điểm

    weather_info:         Optional[WeatherInfo] = None
    user_context_summary: Optional[str]         = None 