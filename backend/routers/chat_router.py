"""
chat_router.py — fixed
Pipeline:
  [NLP] → [Weather] → [DB] → [Scoring] → [AI Generate] → [History] → [Response]

FIXES so với bản cũ:
  FIX-A  Trích xuất `timeopen` từ NLP result (trước đây bị bỏ qua hoàn toàn)
  FIX-B  Tính `check_open_time` và truyền vào user_context cho scoring engine:
         - True  khi user nêu rõ thời điểm ("tối nay") HOẶC muốn lọc đang mở ("bây giờ")
         - False khi user không đề cập → hiển thị cả địa điểm đóng cửa (tìm kiếm tổng quát)
  FIX-C  Đánh số step đúng (8 không bị skip)
"""

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
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
    get_group_db_tags,
    parse_group_type,
    parse_tags,
)
from backend.services.weather_service import (
    WEATHER_CONDITION_VI,
    get_coordinates,
    get_weather_data,
    parse_weather_from_tags,
)
from data.database import get_all_places

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/suggest", tags=["Suggest"])
_engine = RecommenderEngine()

_TZ_HCM = ZoneInfo("Asia/Ho_Chi_Minh")
DEFAULT_COORDS: Tuple[float, float] = (10.7769, 106.7009)  # Trung tâm TP.HCM


# ============================================================================
# HELPERS
# ============================================================================

_TZ_HCM = ZoneInfo("Asia/Ho_Chi_Minh")

def _parse_current_hour(current_time_str: Optional[str]) -> float:
    """
    Chuyển đổi chuỗi thời gian từ NLP (định dạng yyyy-mm-dd hh:mm:ss) thành số thực (float hour).
    Ví dụ: "2026-05-30 14:30:00" -> 14.5
    """
    # Trường hợp chuỗi bị rỗng hoặc lỗi từ phía AI, tự động lấy giờ hiện tại ngoài đời thực của VN
    if not current_time_str:
        now_hcm = datetime.now(tz=_TZ_HCM)
        return now_hcm.hour + now_hcm.minute / 60.0

    try:
        # Ép kiểu và đọc chính xác định dạng chuỗi yyyy-mm-dd hh:mm:ss do Gemini xuất ra
        dt = datetime.strptime(current_time_str.strip(), "%Y-%m-%d %H:%M:%S")
        
        return dt.hour + dt.minute / 60.0
        
    except Exception as e:
        logger.warning(f"[Time Parse] Lỗi không thể parse chuỗi thời gian '{current_time_str}' từ AI: {e}")
        # Fallback: Nếu chuỗi lỗi cấu trúc, app vẫn chạy tiếp bằng cách lấy giờ thực tế
        now_hcm = datetime.now(tz=_TZ_HCM)
        return now_hcm.hour + now_hcm.minute / 60.0


def _build_context_string(nlp: Dict, weather_condition: str, temperature: float) -> str:
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


# ============================================================================
# ROUTES
# ============================================================================

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

    # FIX-A: Trích xuất timeopen (trước đây bị bỏ qua hoàn toàn)
    timeopen: Optional[bool] = nlp.get("timeopen")

    # ── 2. Weather
    weather_condition = "CLEAR"
    temperature       = 28.0
    rain_probability  = 0.0
    weather_source    = "fallback"
    weather_location  = "Trung tâm TP.HCM"

    user_stated = parse_weather_from_tags(tags)
    current_dt  = datetime.now(tz=_TZ_HCM).strftime("%Y-%m-%d %H:%M:%S")

    if user_stated:
        weather_condition = user_stated
        weather_source    = "nlp"
        weather_location  = (nlp_location or "TP.HCM").title()
        logger.info(f"[Weather] Từ NLP: {weather_condition}")
    else:
        try:
            location_query    = nlp_location or "Ho Chi Minh City"
            w                 = await get_weather_data(location_query, current_dt)
            weather_condition = w.weatherCondition
            temperature       = w.temperature
            rain_probability  = w.rainProbability
            weather_source    = "api_name"
            weather_location  = location_query.title()
            logger.info(f"[Weather] API Name→ {weather_condition}, {temperature}°C")
        except Exception as exc:
            logger.warning(f"[Weather] Lỗi API tên, thử GPS: {exc}")
            if payload.location and len(payload.location) == 2:
                try:
                    from backend.services.weather_service import get_weather_by_coords
                    lat, lon          = payload.location[0], payload.location[1]
                    raw_w             = await get_weather_by_coords(lat, lon, current_dt)
                    weather_condition = raw_w["weatherCondition"]
                    temperature       = raw_w["temperature"]
                    rain_probability  = raw_w["rainProbability"]
                    weather_source    = "api_gps"
                    weather_location  = f"{lat:.2f}, {lon:.2f}"
                except Exception as e_gps:
                    logger.warning(f"[Weather] Lỗi GPS: {e_gps}")

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

    # Geocode NLP location → target_coords để location boost hoạt động
    target_coords: Optional[Tuple[float, float]] = None
    if nlp_location:
        try:
            lat_t, lon_t  = await get_coordinates(nlp_location)
            target_coords = (lat_t, lon_t)
            logger.info(f"[LocationBoost] target_coords={target_coords} cho '{nlp_location}'")
        except Exception:
            try:
                lat_t, lon_t  = await get_coordinates(nlp_location)
                target_coords = (lat_t, lon_t)
            except Exception as e_geo:
                logger.warning(f"[LocationBoost] Không geocode được '{nlp_location}': {e_geo}")

    # ── 5. Build must_haves
    must_haves: Dict = {}
    if max_price  is not None: must_haves["budget"]     = max_price
    if min_rating is not None: must_haves["min_rating"] = min_rating

    group_db_tags = get_group_db_tags(tags)
    if group_db_tags:
        must_haves["group_db_tags"] = group_db_tags

    # FIX-A: Ghi nhận timeopen vào must_haves (trước đây bị bỏ qua)
    if timeopen is not None:
        must_haves["timeopen"] = timeopen

    logger.info(
        f"[Filter] budget={must_haves.get('budget')} | "
        f"min_rating={must_haves.get('min_rating')} | "
        f"group_db_tags={must_haves.get('group_db_tags')} | "
        f"timeopen={timeopen}"
    )

    # FIX-B: Tính check_open_time
    # Chỉ lọc theo giờ khi:
    #   - timeopen=True (user muốn chỗ đang mở cửa ngay bây giờ), HOẶC
    #   - current_time_str không phải None (user chỉ định rõ thời điểm như "tối nay")
    # Khi tìm kiếm tổng quát (không đề cập giờ/thời điểm):
    #   → check_open_time = False → hiển thị cả địa điểm đóng cửa
    #   → tránh tình trạng kết quả rỗng khi search lúc đêm khuya
    check_open_time: bool = (timeopen is True) or (current_time_str is not None)

    current_hour = _parse_current_hour(current_time_str)
    user_request = {"must_haves": must_haves, "preferences": parse_tags(tags)}
    user_context = {
        "current_time":    current_hour,
        "weather":         weather_condition,
        "coords":          user_coords,
        "target_coords":   target_coords,
        "check_open_time": check_open_time,   # FIX-B: truyền xuống scoring engine
    }

    logger.info(
        f"[Scoring Input] preferences={user_request['preferences']} | "
        f"current_time={current_hour:.1f}h (HCM) | "
        f"check_open_time={check_open_time} | target_coords={target_coords}"
    )

    # ── 6. Scoring
    top_scored: List[Dict] = await asyncio.to_thread(
        _engine.generate_recommendations, user_request, user_context, all_places
    )

    logger.info(
        f"[Scoring] must_haves={must_haves} | "
        f"weather={weather_condition} | results={len(top_scored)}"
    )

    # Fallback 1: thử lại bỏ group filter
    if not top_scored:
        logger.warning("[Fallback-1] Bỏ group filter, thử lại")
        relaxed = {k: v for k, v in must_haves.items() if k != "group_db_tags"}
        top_scored = await asyncio.to_thread(
            _engine.generate_recommendations,
            {"must_haves": relaxed, "preferences": user_request["preferences"]},
            user_context, all_places,
        )

    # Fallback 2: Top 3 rating thuần
    if not top_scored:
        logger.warning("[Fallback-2] Top 3 theo rating")
        sorted_places = sorted(all_places, key=lambda p: -p.get("rating", 0))
        top_scored = [
            {
                "location_id":    p["id"],
                "name":           p["name"],
                "total_score":    p["rating"],
                "distance_km":    RecommenderEngine._calculate_distance(user_coords, p["coords"]),
                "location_boost": 0.0,
                "matches":        {"styles": [], "moods": []},
            }
            for p in sorted_places[:3]
        ]

    # ── 7. AI Generate (song song)
    place_map   = {p["id"]: p for p in all_places}
    context_str = _build_context_string(nlp, weather_condition, temperature)

    async def _gen(scored_ref: Dict) -> Dict:
        place = place_map.get(scored_ref["location_id"])
        if not place:
            return {"description": "", "fact": ""}
        return await asyncio.to_thread(generate_text, place["name"], place["category"], context_str)

    generated: List[Dict] = await asyncio.gather(*[_gen(r) for r in top_scored])

    # ── 8. Assemble response  (FIX-C: step 8 không bị skip)
    top_places: List[Place] = []
    for scored_ref, gen in zip(top_scored, generated):
        place = place_map.get(scored_ref["location_id"])
        if not place:
            continue
        matches     = scored_ref.get("matches", {})
        hits        = matches.get("moods") or matches.get("styles") or []
        display_tag = hits[0] if hits else place.get("category", "")
        price_val   = place["price"]
        if isinstance(price_val, str):
            price_val = 0 if price_val.lower() in ("free", "") else int(price_val)

        top_places.append(Place(
            id          = place["id"],
            name        = place["name"],
            category    = place["category"],
            tag         = display_tag,
            price       = price_val,
            rating      = place["rating"],
            image_url   = place["image_url"],
            latitude    = place["coords"][0],
            longitude   = place["coords"][1],
            distance    = scored_ref["distance_km"],
            description = gen.get("description", ""),
            fact        = gen.get("fact", ""),
        ))

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

    # ── 9. Lưu lịch sử
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