"""
scoring_service.py
==================
Chịu trách nhiệm toàn bộ logic lọc và chấm điểm địa điểm.

Bugs đã fix (v2):
  - BUG 1: Tags DB tiếng Anh ↔ STYLE/MOOD_TAGS tiếng Việt → bổ sung bảng EN + alias map
  - BUG 2: close_time sau nửa đêm (01:00, 02:00) → thêm midnight-crossing logic
  - BUG 3: Group tags DB là EN (couple/family) ↔ GROUP_TAG_MAP ra tiếng Việt → thêm EN map
"""

import math
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# TAG TABLES — tiếng Việt (NLP input) + tiếng Anh (DB tags)
# ============================================================================

# Style: đặc tính không gian / phong cách (+2.0đ mỗi match)
STYLE_TAGS = {
    # Tiếng Việt (NLP)
    "acoustic", "yên tĩnh", "vắng vẻ", "view đẹp", "sống ảo",
    "không gian xanh", "cổ điển", "hiện đại", "nghệ thuật", "rooftop",
    "tự nhiên", "vintage", "minimalist", "cozy", "sang trọng",
    "bình dân", "đặc sắc", "độc đáo",
    
    "luxury", "artistic", "historical", "cultural", "jazz",
}

# Mood: trạng thái cảm xúc / nhu cầu (+1.0đ mỗi match)
MOOD_TAGS = {
    # Tiếng Việt (NLP)
    "chill", "xả stress", "thư giãn", "lãng mạn", "sôi động",
    "vui vẻ", "khám phá", "cảm giác mạnh", "ăn uống", "hẹn hò",
    "gia đình", "bạn bè", "cặp đôi", "đi một mình", "giải trí",
    "vận động", "học hỏi", "sáng tạo",

    "relax", "romantic", "fun", "energetic", "adventure",
    "nightlife", "educational", "family",
}

# Alias map: NLP tiếng Việt → DB tags tiếng Anh tương đương
# Dùng khi NLP trả về tiếng Việt nhưng DB lưu tiếng Anh
NLP_TO_DB_ALIAS: Dict[str, str] = {
    "thư giãn":      "relax",
    "xả stress":     "relax",
    "lãng mạn":      "romantic",
    "hẹn hò":        "romantic",
    "sôi động":      "energetic",
    "vui vẻ":        "fun",
    "giải trí":      "fun",
    "cảm giác mạnh": "adventure",
    "khám phá":      "adventure",
    "học hỏi":       "educational",
    "vận động":      "energetic",
    "sáng tạo":      "artistic",
    "nghệ thuật":    "artistic",
    "sang trọng":    "luxury",
    "ban đêm":       "nightlife",
    "về đêm":        "nightlife",
    "ăn uống":       "food",
}

# ============================================================================
# GROUP TAG MAP — tiếng Việt (NLP) → cả VN lẫn EN để match DB  ← FIX BUG 3
# ============================================================================
# Map: từ NLP → danh sách tag có thể có trong DB
GROUP_TAG_MAP: Dict[str, List[str]] = {
    "cặp đôi":   ["couple", "cặp đôi"],
    "đôi":       ["couple", "cặp đôi"],
    "bồ":        ["couple", "cặp đôi"],
    "người yêu": ["couple", "cặp đôi"],
    "hẹn hò":    ["couple", "cặp đôi"],
    "gia đình":  ["family", "gia đình"],
    "ba mẹ":     ["family", "gia đình"],
    "con cái":   ["family", "kids", "gia đình"],
    "trẻ em":    ["kids", "family"],
    "bạn bè":    ["friends", "bạn bè"],
    "hội bạn":   ["friends", "bạn bè"],
    "hội":       ["friends", "bạn bè"],
    "nhóm bạn":  ["friends", "bạn bè"],
    "một mình":  ["solo", "đi một mình"],
    "solo":      ["solo", "đi một mình"],
}

# Map ngược: từ NLP keyword → canonical group name (dùng để build context summary)
GROUP_DISPLAY_MAP: Dict[str, str] = {
    "cặp đôi": "Cặp đôi", "đôi": "Cặp đôi", "bồ": "Cặp đôi",
    "người yêu": "Cặp đôi", "hẹn hò": "Cặp đôi",
    "gia đình": "Gia đình", "ba mẹ": "Gia đình", "con cái": "Gia đình", "trẻ em": "Gia đình",
    "bạn bè": "Hội bạn", "hội bạn": "Hội bạn", "hội": "Hội bạn", "nhóm bạn": "Hội bạn",
    "một mình": "Đi một mình", "solo": "Đi một mình",
}


def parse_tags(nlp_tags: List[str]) -> Dict[str, List[str]]:
    """
    Phân loại NLP tags → style / mood, đồng thời mở rộng alias VN→EN.
    Returns: {"style": [...], "mood": [...]}
    """
    style_list, mood_list = [], []
    for tag in nlp_tags:
        normalized = tag.lower().strip()
        # Mở rộng alias
        alias = NLP_TO_DB_ALIAS.get(normalized)
        candidates = {normalized}
        if alias:
            candidates.add(alias)

        for c in candidates:
            if c in STYLE_TAGS:
                style_list.append(c)
                break
            elif c in MOOD_TAGS:
                mood_list.append(c)
                break
        else:
            # Tag không khớp gì → đưa vào mood (fallback, vẫn có giá trị gợi ý)
            mood_list.append(normalized)

    return {"style": list(dict.fromkeys(style_list)), "mood": list(dict.fromkeys(mood_list))}


def parse_group_type(nlp_tags: List[str]) -> Optional[str]:
    """
    Tìm group type đầu tiên khớp.
    Trả về canonical name (VD: "Cặp đôi") để hiển thị context summary.
    """
    for tag in nlp_tags:
        key = tag.lower().strip()
        if key in GROUP_DISPLAY_MAP:
            return GROUP_DISPLAY_MAP[key]
    return None


def get_group_db_tags(nlp_tags: List[str]) -> Optional[List[str]]:
    """
    Trả về list DB tags cần check (VD: ["couple","cặp đôi"]).
    Dùng trong hard filter để so sánh với loc["tags"].
    """
    for tag in nlp_tags:
        key = tag.lower().strip()
        if key in GROUP_TAG_MAP:
            return GROUP_TAG_MAP[key]
    return None


# ============================================================================
# SCORING ENGINE
# ============================================================================

class RecommenderEngine:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {
            "weights": {
                "style":    2.0,
                "mood":     1.0,
                "distance": -0.2,
            },
            "weather_rules": {
                "bad_weather_statuses":      ["RAIN", "STORM", "DRIZZLE"],
                "restricted_location_types": ["outdoor", "Outdoor"],
            },
            "max_results": 3,
        }

    # ── Haversine ────────────────────────────────────────────────────────────

    @staticmethod
    def _calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        lat1, lon1 = coord1
        lat2, lon2 = coord2
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

    # ── Hard filter ──────────────────────────────────────────────────────────

    def _is_open(self, open_t: float, close_t: float, current_hour: float) -> bool:
        """
        Kiểm tra giờ mở cửa. Xử lý trường hợp đóng cửa sau nửa đêm.  ← FIX BUG 2
        VD: open=17.5, close=2.0 → open midnight-crossing
        """
        if open_t <= close_t:
            # Bình thường: 09:00 → 22:00
            return open_t <= current_hour <= close_t
        else:
            # Vượt nửa đêm: 19:00 → 01:00
            return current_hour >= open_t or current_hour <= close_t

    def _passes_hard_filter(
        self,
        loc: Dict,
        must_haves: Dict,
        current_time: float,
        weather: str,
    ) -> bool:
        # Giờ mở cửa
        if not self._is_open(
            loc.get("open_time", 0),
            loc.get("close_time", 24),
            current_time
        ):
            return False

        # Ngân sách
        if "budget" in must_haves and loc.get("price", 0) > must_haves["budget"]:
            return False

        # Thời tiết: loại outdoor khi trời xấu
        bad_weather = self.config["weather_rules"]["bad_weather_statuses"]
        restricted  = self.config["weather_rules"]["restricted_location_types"]
        if weather in bad_weather and loc.get("type", "").lower() in [t.lower() for t in restricted]:
            return False

        # Loại hình cụ thể
        if must_haves.get("category") and loc.get("category") != must_haves["category"]:
            return False

        # Rating tối thiểu
        if must_haves.get("min_rating") and loc.get("rating", 0) < must_haves["min_rating"]:
            return False

        # Nhóm người: so sánh với cả EN lẫn VN tags  ← FIX BUG 3
        required_group_tags = must_haves.get("group_db_tags")  # list[str]
        if required_group_tags:
            loc_tags_lower = [t.lower() for t in loc.get("tags", [])]
            # Nếu KHÔNG có bất kỳ tag nào trong list → loại
            if not any(g.lower() in loc_tags_lower for g in required_group_tags):
                return False

        return True

    # ── Soft scoring ─────────────────────────────────────────────────────────

    def _score(self, loc: Dict, preferences: Dict[str, List[str]], user_coords: Tuple) -> Dict:
        score = loc.get("rating", 0.0)
        matched_styles, matched_moods = [], []

        loc_tags_lower = [t.lower() for t in loc.get("tags", [])]

        for tag in loc_tags_lower:
            # Check cả alias ngược: DB tag → có trong preference không
            if tag in preferences.get("style", []):
                score += self.config["weights"]["style"]
                matched_styles.append(tag)
            elif tag in preferences.get("mood", []):
                score += self.config["weights"]["mood"]
                matched_moods.append(tag)

        distance = self._calculate_distance(user_coords, loc["coords"])
        score += distance * self.config["weights"]["distance"]

        return {
            "location_id": loc.get("id"),
            "name":        loc.get("name"),
            "total_score": round(score, 2),
            "distance_km": distance,
            "matches": {
                "styles": matched_styles,
                "moods":  matched_moods,
            },
        }

    # ── Main entry point ─────────────────────────────────────────────────────

    def generate_recommendations(
        self,
        user_request: Dict,
        user_context: Dict,
        location_database: List[Dict],
    ) -> List[Dict]:
        must_haves   = user_request.get("must_haves", {})
        preferences  = user_request.get("preferences", {})
        current_time = user_context["current_time"]
        weather      = user_context.get("weather", "CLEAR")
        user_coords  = user_context["coords"]

        valid = [
            loc for loc in location_database
            if self._passes_hard_filter(loc, must_haves, current_time, weather)
        ]

        scored = [self._score(loc, preferences, user_coords) for loc in valid]
        scored.sort(key=lambda x: (-x["total_score"], x["distance_km"]))

        return scored[: self.config["max_results"]]