"""
Pipeline:
  [NLP] → [Weather] → [DB] → [Scoring] → [AI Generate] → [History] → [Response]
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException

from backend.core.config import settings
from backend.dependencies.auth import get_optional_user
from backend.schemas.request_schema import SuggestionRequest
from backend.schemas.response_schema import Place, SuggestionResponse, WeatherInfo
from backend.services.ai_service import extract_nlp_intent, generate_text
from backend.services.history_service import get_history as svc_get_history
from backend.services.history_service import save_history
from backend.services.scoring_service import (
    RecommenderEngine,
    parse_group_type,
    parse_tags,
)
from backend.services.weather_service import (
    WEATHER_CONDITION_VI,
    get_weather_data,
    parse_weather_from_tags,
)
from data.database import get_all_places

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/suggest", tags=["Suggest"])

_engine = RecommenderEngine()

DEFAULT_COORDS: Tuple[float, float] = (10.7769, 106.7009)  # Trung tâm TP.HCM


# HELPERS — điều phối
# ============================================================================
def _parse_current_hour(current_time_str: Optional[str]) -> float:
    """Chuyển NLP current_time string → float hour."""
    now = datetime.now().hour + datetime.now().minute / 60
    if not current_time_str or current_time_str.lower() == "now":
        return now
    t = current_time_str.lower()
    if any(w in t for w in ["tối", "evening"]):   return 20.0
    if any(w in t for w in ["sáng", "morning"]):  return 9.0
    if any(w in t for w in ["trưa", "noon"]):      return 12.0
    if any(w in t for w in ["chiều", "afternoon"]): return 15.0
    if any(w in t for w in ["đêm", "khuya", "night"]): return 22.0
    return now


def _build_context_string(nlp: Dict, weather_condition: str, temperature: float) -> str:
    """Tạo chuỗi ngữ cảnh ngắn truyền vào generate_text()."""
    parts = []
    if nlp.get("tags"):
        parts.append(f"Tâm trạng/nhu cầu: {', '.join(nlp['tags'][:5])}")
    if nlp.get("max_price"):
        parts.append(f"Ngân sách: {nlp['max_price']:,}đ")
    if weather_condition:
        vn = WEATHER_CONDITION_VI.get(weather_condition, weather_condition)
        parts.append(f"Thời tiết: {vn}, {temperature:.0f}°C")
    if nlp.get("location"):
        parts.append(f"Khu vực: {nlp['location']}")
    return " | ".join(parts) if parts else "Du khách tại TP.HCM"


def _build_context_summary(nlp: Dict) -> str:
    """Tạo chuỗi tóm tắt ngắn hiển thị trên UI. VD: 'Chill · Cặp đôi · 200k'"""
    parts = []
    if nlp.get("tags"):
        parts.append(nlp["tags"][0].capitalize())
    group = parse_group_type(nlp.get("tags") or [])
    if group:
        parts.append(group)
    if nlp.get("max_price"):
        price = nlp["max_price"]
        parts.append(f"{price // 1000}k" if price >= 1000 else f"{price}đ")
    if nlp.get("location"):
        parts.append(nlp["location"])
    return " · ".join(parts)


@router.post("", response_model=SuggestionResponse)
async def get_suggestions(
    payload: SuggestionRequest,
    user: Optional[dict] = Depends(get_optional_user),
):
    user_label = user.get("email") if user else "Guest"
    logger.info(f"[Suggest] User={user_label} | Query='{payload.query}'")

    # ── 1. NLP
    nlp: Dict = await asyncio.to_thread(extract_nlp_intent, payload.query)
    logger.info(f"[NLP] {nlp}")

    tags:             List[str]       = nlp.get("tags") or []
    max_price:        Optional[int]   = nlp.get("max_price")
    min_rating:       Optional[float] = nlp.get("min_rating")
    current_time_str: Optional[str]   = nlp.get("current_time")
    nlp_location:     Optional[str]   = nlp.get("location")

    # ── 2. Weather
    weather_condition = "CLEAR"
    temperature       = 28.0
    rain_probability  = 0.0
    weather_source    = "fallback"
    weather_location  = "Trung tâm TP.HCM"

    user_stated = parse_weather_from_tags(tags)

    if user_stated:
        weather_condition = user_stated
        weather_source    = "nlp"
        weather_location  = nlp_location.title()
        logger.info(f"[Weather] Từ NLP: {weather_condition}")
    else:
        try:
            location_query = nlp_location or "Ho Chi Minh City"
            current_dt     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            w              = await get_weather_data(location_query, current_dt)

            weather_condition = w.weatherCondition
            temperature       = w.temperature
            rain_probability  = w.rainProbability
            weather_source    = "api_name"
            weather_location  = location_query.title()
            logger.info(f"[Weather] API Name→ {weather_condition}, {temperature}°C")
        except Exception as exc:
            logger.warning(f"[Weather] Lỗi API tên, thử dùng GPS user: {exc}")
            if payload.location and len(payload.location) == 2:
                try:
                    from backend.services.weather_service import get_weather_by_coords
                    lat, lon = payload.location[0], payload.location[1]
                    raw_w = await get_weather_by_coords(lat, lon, current_dt)

                    weather_condition = raw_w["weatherCondition"]
                    temperature       = raw_w["temperature"]
                    rain_probability  = raw_w["rainProbability"]
                    weather_source    = "api_gps"
                    weather_location  = f"{lat:.2f}, {lon:.2f}"
                    logger.info(f"[Weather] API GPS→ {weather_condition}, {temperature}°C")
                except Exception as e_gps:
                    logger.warning(f"[Weather] Lỗi API GPS: {e_gps}")

    # ── 3. Load DB 
    all_places: List[Dict] = await asyncio.to_thread(get_all_places)
    if not all_places:
        raise HTTPException(status_code=503, detail="Không thể tải dữ liệu địa điểm.")

    # ── 4. Build scoring input 
    user_coords: Tuple[float, float] = (
        (payload.location[0], payload.location[1])
        if payload.location and len(payload.location) == 2
        else DEFAULT_COORDS
    )

    must_haves: Dict = {}
    if max_price  is not None: must_haves["budget"]     = max_price
    if min_rating is not None: must_haves["min_rating"] = min_rating
    group = parse_group_type(tags)
    if group: must_haves["group_type"] = group

    user_request = {"must_haves": must_haves, "preferences": parse_tags(tags)}
    user_context = {
        "current_time": _parse_current_hour(current_time_str),
        "weather":      weather_condition,
        "coords":       user_coords,
    }

    # ── 5. Scoring 
    top_scored: List[Dict] = await asyncio.to_thread(
        _engine.generate_recommendations, user_request, user_context, all_places
    )

    logger.info(
        f"[Scoring] must_haves={must_haves} | "
        f"preferences={user_request['preferences']} | "
        f"current_time={user_context['current_time']:.1f}h | "
        f"weather={weather_condition} | "
        f"results={len(top_scored)}"
    )

    # Fallback: bỏ filter, lấy Top 3 theo rating nếu lọc hết
    if not top_scored:
        logger.warning("[Scoring] Không có kết quả → fallback Top 3 theo rating")
        sorted_places = sorted(all_places, key=lambda p: -p.get("rating", 0))
        top_scored = [
            {
                "location_id": p["id"],
                "name":        p["name"],
                "total_score": p["rating"],
                "distance_km": RecommenderEngine._calculate_distance(user_coords, p["coords"]),
                "matches":     {"styles": [], "moods": []},
            }
            for p in sorted_places[:3]
        ]

    # ── 6. AI Generate (song song)
    place_map = {p["id"]: p for p in all_places}
    context_str = _build_context_string(nlp, weather_condition, temperature)

    async def _gen(scored_ref: Dict) -> Dict:
        place = place_map.get(scored_ref["location_id"])
        if not place:
            return {"description": "", "fact": ""}
        return await asyncio.to_thread(
            generate_text, place["name"], place["category"], context_str
        )

    generated: List[Dict] = await asyncio.gather(*[_gen(r) for r in top_scored])

    # ── 7. Assemble response
    top_places: List[Place] = []
    for scored_ref, gen in zip(top_scored, generated):
        place = place_map.get(scored_ref["location_id"])
        if not place:
            continue

        matches    = scored_ref.get("matches", {})
        hits       = matches.get("moods") or matches.get("styles") or []
        display_tag = hits[0] if hits else place.get("category", "")

        top_places.append(Place(
            id          = place["id"],
            name        = place["name"],
            category    = place["category"],
            tag         = display_tag,
            price       = place["price"],
            rating      = place["rating"],
            image_url   = place["image_url"],
            latitude    = place["coords"][0],
            longitude   = place["coords"][1],
            distance    = scored_ref["distance_km"],
            description = gen.get("description", ""),
            fact        = gen.get("fact", ""),
        ))

    # ── 8. Tạo Response Object
    response_obj = SuggestionResponse(
        status               = "success",
        message              = f"Tìm thấy {len(top_places)} địa điểm phù hợp!",
        top_places           = top_places,
        weather_info         = WeatherInfo(
            condition        = weather_condition,
            condition_vi     = WEATHER_CONDITION_VI.get(weather_condition, ""),
            temperature      = temperature,
            rain_probability = rain_probability,
            source           = weather_source,
            location_name    = weather_location,
        ),
        user_context_summary = _build_context_summary(nlp),
    )

    # ── 9. Lưu lịch sử toàn bộ payload
    if user and top_scored:
        asyncio.create_task(
            asyncio.to_thread(save_history, user["uid"], payload.query, response_obj.model_dump())
        )

    return response_obj

@router.get("/history")
async def get_history(
    limit: int = 5,
    user: Optional[dict] = Depends(get_optional_user),
):
    if not user:
        return {"message": "Vui lòng đăng nhập để xem lịch sử.", "history": []}

    history = await asyncio.to_thread(svc_get_history, user["uid"], limit)
    return {"message": f"Lịch sử của {user.get('email')}", "history": history}