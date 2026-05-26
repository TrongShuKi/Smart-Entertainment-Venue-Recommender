"""
scoring_service.py — v6 (Fixed DB Tags Mapping)
=====================================
FIXES so với v5:
  FIX-7  _passes_hard_filter: Lấy dữ liệu từ loc["group_tags"] thay vì loc["tags"] (vì DB đã tách cột)
  FIX-8  _score: Lấy thẳng loc["mood_tags"] để chấm điểm thay vì phải lọc tay từ loc["tags"]
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


# ============================================================================
# TAG TABLES — khớp CHÍNH XÁC với tags trong DB (toàn EN lowercase)
# ============================================================================

STYLE_TAGS = {
    # Phong cách không gian / thẩm mỹ / kiến trúc / văn hóa
    "vintage", "luxury", "artistic", "historical", "cultural", "culture",
    "jazz", "rooftop", "acoustic", "minimalist", "cozy",
    "instagrammable", "scenic", "panoramic", "majestic", "nostalgic",
    "modern", "authentic", "solemn", "mysterious", "architecture",
    "architectural", "colorful", "cute", "handmade", "traditional",
    "historic", "history",
}

MOOD_TAGS = {
    # Cảm giác / Trạng thái
    "chill", "relax", "relaxing", "romantic", "fun", "energetic",
    "lively", "bustling", "peaceful", "quiet", "healing", "wellness",
    "meditation", "spa", "resort", "cool", "cool_weather",

    # Hoạt động ngoài trời / Thiên nhiên
    "adventure", "adventurous", "active", "hiking", "trekking",
    "cycling", "swimming", "camping", "picnic", "beach", "seaside",
    "snorkeling", "diving", "boating", "boat_trip", "sandboarding",
    "zipline", "extreme", "thrill", "thrilling", "walk", "walking",
    "exercise", "water_activity", "water_fun", "water_games",
    "waterpark", "waterfall", "birdwatching", "wildlife",
    "cave_exploration", "cloud_hunting", "cloud_view",

    # Hoạt động / Trải nghiệm (Đã lọc các từ trùng với STYLE_TAGS)
    "educational", "intellectual", "spiritual", "patriotic",
    "community", "local_experience", "local_food", "local_life",
    "countryside", "ecotourism", "eco", "biodiversity",
    "river_life", "sightseeing", "exploration", "explore",

    # Ẩm thực / Giải trí / Check-in
    "food", "foodie", "seafood", "beer", "shopping", "entertainment",
    "nightlife", "party", "music", "show", "gaming",
    "animal_show", "folk_games", "festival", "interactive", "creative",
    "photography", "photo", "checkin",

    # Cảnh quan
    "nature", "green_space", "mountain_view", "sunrise", "sunset", 
    "night_view", "nightview", "flower_field", "fruit_garden", "clear_water",

    # Misc
    "emotional", "fantasy", "weird", "spectacular", "transit",
}

# Group tags trong DB — loại ra khỏi mood/style scoring
GROUP_TAGS_DB = {
    "adventurers", "business", "children", "couple", "elderly", 
    "family", "foreigners", "friends", "group", "kids", 
    "solo", "student", "students", "teen", "teens", "tourist"
}

# ============================================================================
# ALIAS NLP → DB — multi-value (một VN term → nhiều EN DB tags)
# ============================================================================

NLP_TO_DB_ALIAS: Dict[str, Union[str, List[str]]] = {
    # Thư giãn
    "thư giãn":        ["relax", "chill", "relaxing", "peaceful"],
    "xả stress":       ["relax", "chill", "wellness", "healing"],
    "nghỉ ngơi":       ["relax", "resort", "peaceful"],
    "bình yên":        ["peaceful", "quiet", "relax"],
    "yên tĩnh":        ["peaceful", "quiet"],
    "vắng vẻ":         ["peaceful", "quiet"],
    "tĩnh lặng":       ["peaceful", "meditation"],

    # Vui vẻ / Năng động
    "vui vẻ":          ["fun", "lively", "entertaining"],
    "sôi động":        ["energetic", "lively", "bustling", "fun"],
    "náo nhiệt":       ["bustling", "lively", "nightlife", "energetic"],
    "giải trí":        ["entertainment", "fun", "show", "gaming"],
    "vận động":        ["active", "energetic", "exercise"],

    # Hẹn hò / Lãng mạn
    "lãng mạn":        ["romantic", "scenic", "sunset", "chill"],
    "hẹn hò":          ["romantic", "chill", "scenic"],
    "tình nhân":       ["romantic", "scenic"],

    # Ẩm thực
    "ăn uống":         ["food", "foodie", "local_food"],
    "ẩm thực":         ["food", "foodie", "local_food", "seafood"],
    "đặc sản":         ["local_food", "authentic", "foodie"],
    "hải sản":         ["seafood", "food", "beach"],
    "đồ ăn ngon":      ["foodie", "food", "local_food"],
    "ngon":            ["food", "foodie", "local_food"],
    "quán ăn ngon":    ["food", "foodie"],
    "giá rẻ":          ["local_experience", "local_food", "authentic"],

    # Thiên nhiên
    "thiên nhiên":     ["nature", "eco", "green_space", "peaceful"],
    "không gian xanh": ["nature", "green_space", "eco"],
    "tự nhiên":        ["nature", "eco", "wildlife"],
    "sinh thái":       ["eco", "ecotourism", "nature", "wildlife"],
    "cây xanh":        ["nature", "green_space"],

    # Biển / Núi / Thác
    "biển":            ["beach", "seaside", "clear_water", "swimming"],
    "thác nước":       ["waterfall", "nature", "eco"],
    "thác":            ["waterfall", "nature"],
    "núi":             ["mountain_view", "trekking", "nature"],
    "leo núi":         ["hiking", "trekking", "adventurous", "active"],
    "khám phá":        ["adventure", "exploration", "explore"],

    # Cảm giác mạnh
    "cảm giác mạnh":   ["adventurous", "extreme", "thrilling", "thrill"],
    "mạo hiểm":        ["adventurous", "extreme", "adventure"],
    "phiêu lưu":       ["adventure", "adventurous", "exploration"],

    # Văn hoá / Lịch sử
    "học hỏi":         ["educational", "cultural", "historical", "history"],
    "văn hoá":         ["cultural", "culture", "historical", "authentic"],
    "văn hóa":         ["cultural", "culture", "historical", "authentic"], 
    "lịch sử":         ["historical", "history", "historic", "cultural"],
    "tâm linh":        ["spiritual", "solemn", "meditation"],
    "nghệ thuật":      ["artistic", "creative", "cultural", "instagrammable"],
    "di tích":         ["historical", "history", "historic"],
    "di tích lịch sử": ["historical", "history", "historic", "cultural"],
    "bảo tàng":        ["educational", "historical", "intellectual", "culture"],
    
    # Giá cả (Thêm mới nhẹ để chấm điểm không gian công cộng)
    "miễn phí":        ["local_experience", "walk", "chill"], 
    "free":            ["local_experience", "walk"],

    # Phong cách / Thẩm mỹ
    "sang trọng":      ["luxury", "scenic", "rooftop"],
    "cổ điển":         ["vintage", "nostalgic", "historical"],
    "hiện đại":        ["modern", "luxury", "instagrammable"],
    "độc đáo":         ["authentic", "weird", "instagrammable"],
    "đặc sắc":         ["authentic", "instagrammable"],
    "sáng tạo":        ["creative", "artistic", "interactive"],

    # Ảnh / Check-in
    "chụp ảnh":        ["photography", "photo", "checkin", "instagrammable"],
    "sống ảo":         ["instagrammable", "photo", "checkin", "scenic"],
    "view đẹp":        ["scenic", "panoramic", "instagrammable", "sunset"],
    "check in":        ["checkin", "instagrammable", "photography"],

    # Ban đêm
    "ban đêm":         ["nightlife", "night_view", "nightview"],
    "về đêm":          ["nightlife", "night_view", "chill"],
    "đêm":             ["nightlife", "night_view"],

    # Mua sắm
    "mua sắm":         ["shopping", "entertainment"],

    # Thể thao / Sức khoẻ
    "thể thao":        ["active", "exercise", "energetic"],
    "yoga":            ["meditation", "wellness", "peaceful"],
    "spa":             ["spa", "wellness", "relaxing"],
    "chữa lành":       ["healing", "wellness", "peaceful", "nature"],

    # HỌC TẬP/LÀM VIỆC:
    "học bài":          ["quiet", "student", "cozy", "chill"],
    "làm việc":         ["quiet", "business", "minimalist", "peaceful"],
    "chạy deadline":    ["quiet", "student", "business", "chill"],
    "đọc sách":         ["quiet", "peaceful", "intellectual", "cozy"],

    # Hoạt dộng
    "đi dạo":          ["walk", "walking", "chill", "peaceful"],
    "đi dạo phố":      ["walk", "walking", "chill", "peaceful"],
    "đi bộ":           ["walk", "walking", "active"],
    "dạo phố":         ["walk", "walking", "chill", "sightseeing"],
    "tản bộ":          ["walk", "walking", "relax"],
    "hóng gió":        ["chill", "relax", "scenic"],
    "ngắm cảnh":       ["scenic", "sightseeing", "panoramic", "nature"],
    "ngắm cảnh đẹp":   ["scenic", "sightseeing", "panoramic", "instagrammable"],

    # Nhóm Đi chơi / Giải trí chung chung
    "đi chơi":  ["fun", "entertainment", "chill", "explore"],
    "chơi":     ["fun", "entertainment", "lively"],
    "đi lượn":  ["chill", "walk", "sightseeing"],
    "đi quẩy":  ["party", "nightlife", "lively", "energetic"],

    # Địa phương
    "bình dân":        ["local_experience", "local_food", "authentic"],
    "địa phương":      ["local_experience", "local_food", "local_life"],
    "dân dã":          ["local_life", "authentic", "countryside"],
    "nông thôn":       ["countryside", "eco", "local_life"],

    # Thời tiết (pass-through)
    "mưa":             "relax",
    "nắng":            "beach",
    "trời nắng":       "beach",
    "nắng đẹp":        "scenic",
}

# VN group keywords — filter ra khỏi mood/style hoàn toàn
GROUP_KEYWORDS_VN = {
    "cặp đôi", "đôi", "bồ", "người yêu",
    "gia đình", "ba mẹ", "con cái", "trẻ em",
    "bạn bè", "hội bạn", "hội", "nhóm bạn",
    "một mình",
    "sinh viên", "học sinh"
}

# ============================================================================
# GROUP TAG MAP
# ============================================================================

GROUP_TAG_MAP: Dict[str, List[str]] = {
    "cặp đôi":   ["couple"],
    "đôi":       ["couple"],
    "bồ":        ["couple"],
    "người yêu": ["couple"],
    "hẹn hò":    ["couple"],
    "gia đình":  ["family"],
    "ba mẹ":     ["family"],
    "con cái":   ["family", "kids"],
    "trẻ em":    ["kids", "family", "children"],
    "bạn bè":    ["friends"],
    "hội bạn":   ["friends"],
    "hội":       ["friends"],
    "nhóm bạn":  ["friends"],
    "một mình":  ["solo"],
    "solo":      ["solo"],
}

GROUP_DISPLAY_MAP: Dict[str, str] = {
    "cặp đôi":   "Cặp đôi",
    "đôi":       "Cặp đôi",
    "bồ":        "Cặp đôi",
    "người yêu": "Cặp đôi",
    "hẹn hò":    "Cặp đôi",
    "gia đình":  "Gia đình",
    "ba mẹ":     "Gia đình",
    "con cái":   "Gia đình",
    "trẻ em":    "Gia đình",
    "bạn bè":    "Hội bạn",
    "hội bạn":   "Hội bạn",
    "hội":       "Hội bạn",
    "nhóm bạn":  "Hội bạn",
    "một mình":  "Đi một mình",
    "solo":      "Đi một mình",
}

# ============================================================================
# PUBLIC HELPERS
# ============================================================================

def parse_tags(nlp_tags: List[str]) -> Dict[str, List[str]]:
    """
    Phân loại NLP tags → {"style": [...], "mood": [...]}.
    """
    style_list, mood_list = [], []
    all_group_kw = GROUP_TAGS_DB | GROUP_KEYWORDS_VN

    for tag in nlp_tags:
        normalized = tag.lower().strip()

        if normalized in all_group_kw:
            continue  # group keyword → bỏ qua

        resolved = NLP_TO_DB_ALIAS.get(normalized, normalized)
        en_tags: List[str] = resolved if isinstance(resolved, list) else [resolved]

        for en_tag in en_tags:
            if en_tag in STYLE_TAGS:
                style_list.append(en_tag)
            elif en_tag in MOOD_TAGS:
                mood_list.append(en_tag)
            else:
                mood_list.append(en_tag)  # soft fallback

    return {
        "style": list(dict.fromkeys(style_list)),
        "mood":  list(dict.fromkeys(mood_list)),
    }


def parse_group_type(nlp_tags: List[str]) -> Optional[str]:
    """Trả về display name group. VD: "Cặp đôi"."""
    for tag in nlp_tags:
        key = tag.lower().strip()
        if key in GROUP_DISPLAY_MAP:
            return GROUP_DISPLAY_MAP[key]
    return None


def get_group_db_tags(nlp_tags: List[str]) -> Optional[List[str]]:
    """Trả về list EN group tags để filter DB["tags"]. VD: ["solo"]."""
    for tag in nlp_tags:
        key = tag.lower().strip()
        if key in GROUP_TAG_MAP:
            return GROUP_TAG_MAP[key]
    return None


# ============================================================================
# SCORING ENGINE
# ============================================================================

_LOCATION_RADIUS_KM = 8.0


def _to_float_hour(val) -> float:
    """Chuyển open/close time về float. DB lưu "HH:MM:SS" hoặc float."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        parts = val.strip().split(":")
        try:
            return int(parts[0]) + (int(parts[1]) if len(parts) > 1 else 0) / 60.0
        except (ValueError, IndexError):
            return 0.0
    return 0.0


def _is_purely_outdoor(space_type: str) -> bool:
    """
    Xác định địa điểm là "chỉ ngoài trời" để block khi thời tiết xấu.
    """
    st = space_type.lower().strip()
    if not st:
        return False
    if "indoor" in st:
        return False
    return st in ("outdoor", "underground")


class RecommenderEngine:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {
            "weights": {
                "style":          2.0,
                "mood":           1.0,
                "distance":      -0.15,
                "location_boost": 2.0,
            },
            "weather_rules": {
                "bad_weather_statuses": ["RAIN", "STORM", "DRIZZLE"],
            },
            "max_results": 3,
        }

    @staticmethod
    def _calculate_distance(c1: Tuple[float, float], c2: Tuple[float, float]) -> float:
        lat1, lon1 = c1
        lat2, lon2 = c2
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)

    def _is_open(self, open_t, close_t, current_hour: float) -> bool:
        open_f  = _to_float_hour(open_t)
        close_f = _to_float_hour(close_t)
        if open_f <= close_f:
            return open_f <= current_hour <= close_f
        return current_hour >= open_f or current_hour <= close_f  # midnight-crossing

    def _passes_hard_filter(
        self,
        loc: Dict,
        must_haves: Dict,
        current_time: float,
        weather: str,
        check_open_time: bool = False,
    ) -> bool:

        if check_open_time:
            if not self._is_open(loc.get("open_time"), loc.get("close_time", 23.99), current_time):
                logger.debug(
                    f"[TimeFilter] LOẠI '{loc.get('name')}' "
                    f"(open={loc.get('open_time')}, close={loc.get('close_time')}, "
                    f"now={current_time:.1f}h)"
                )
                return False

        price = loc.get("price", 0)
        if isinstance(price, str):
            price = 0 if price.lower() in ("free", "") else int(price)
        if "budget" in must_haves and price > must_haves["budget"]:
            return False

        if weather in self.config["weather_rules"]["bad_weather_statuses"]:
            loc_type = loc.get("type", "")
            if _is_purely_outdoor(loc_type):
                logger.debug(
                    f"[WeatherFilter] LOẠI '{loc.get('name')}' type='{loc_type}' weather='{weather}'"
                )
                return False

        if must_haves.get("min_rating") and loc.get("rating", 0) < must_haves["min_rating"]:
            return False

        # FIX-7: Group filter — lấy dữ liệu trực tiếp từ "group_tags"
        required_group = must_haves.get("group_db_tags")
        if required_group:
            loc_group_tags = [t.lower() for t in loc.get("group_tags", [])]
            if not any(g in loc_group_tags for g in required_group):
                return False

        return True

    def _score(
        self,
        loc: Dict,
        preferences: Dict[str, List[str]],
        user_coords: Tuple[float, float],
        target_coords: Optional[Tuple[float, float]] = None,
    ) -> Dict:
        score = loc.get("rating", 0.0)
        matched_styles, matched_moods = [], []

        # FIX-8: Lấy thẳng "mood_tags" để chấm điểm, bỏ qua việc phải phân tách lọc thủ công
        scorable = [t.lower() for t in loc.get("mood_tags", [])]

        for tag in scorable:
            if tag in preferences.get("style", []):
                score += self.config["weights"]["style"]
                matched_styles.append(tag)
            elif tag in preferences.get("mood", []):
                score += self.config["weights"]["mood"]
                matched_moods.append(tag)

        distance = self._calculate_distance(user_coords, loc["coords"])
        score   += distance * self.config["weights"]["distance"]

        location_boost = 0.0
        if target_coords:
            dist_to_target = self._calculate_distance(target_coords, loc["coords"])
            if dist_to_target <= _LOCATION_RADIUS_KM:
                location_boost = self.config["weights"]["location_boost"]
                score         += location_boost
                logger.debug(
                    f"[LocationBoost] +{location_boost} '{loc.get('name')}' "
                    f"dist_to_target={dist_to_target:.1f}km"
                )

        return {
            "location_id":    loc.get("id"),
            "name":           loc.get("name"),
            "total_score":    round(score, 2),
            "distance_km":    distance,
            "location_boost": location_boost,
            "matches": {
                "styles": matched_styles,
                "moods":  matched_moods,
            },
        }

    def generate_recommendations(
        self,
        user_request: Dict,
        user_context: Dict,
        location_database: List[Dict],
    ) -> List[Dict]:
        must_haves    = user_request.get("must_haves", {})
        preferences   = user_request.get("preferences", {})
        current_time  = user_context["current_time"]
        weather       = user_context.get("weather", "CLEAR")
        user_coords   = user_context["coords"]
        target_coords = user_context.get("target_coords")

        check_open_time = user_context.get("check_open_time", False)

        valid = [
            loc for loc in location_database
            if self._passes_hard_filter(loc, must_haves, current_time, weather, check_open_time)
        ]

        logger.info(
            f"[Scoring] {len(valid)}/{len(location_database)} địa điểm qua hard filter "
            f"(check_open_time={check_open_time})"
        )

        scored = [
            self._score(loc, preferences, user_coords, target_coords)
            for loc in valid
        ]
        scored.sort(key=lambda x: (-x["total_score"], x["distance_km"]))

        return scored[: self.config["max_results"]]