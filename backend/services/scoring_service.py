"""
scoring_service.py
==================
Chịu trách nhiệm toàn bộ logic lọc và chấm điểm địa điểm:
  - STYLE_TAGS / MOOD_TAGS    : Bảng phân loại tag (chuyển về từ chat_router)
  - GROUP_TAG_MAP             : Map cách nói thông thường → group_type chuẩn
  - parse_tags()              : Phân loại NLP tags → style / mood
  - parse_group_type()        : Trích xuất group type từ NLP tags
  - RecommenderEngine         : Lọc cứng + chấm điểm có trọng số → Top N
"""

import math
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# Style (+2.0đ): đặc tính không gian / phong cách vật lý cụ thể
STYLE_TAGS = {
    "acoustic", "yên tĩnh", "vắng vẻ", "view đẹp", "sống ảo",
    "không gian xanh", "cổ điển", "hiện đại", "nghệ thuật", "rooftop",
    "tự nhiên", "vintage", "minimalist", "cozy", "sang trọng",
    "bình dân", "đặc sắc", "độc đáo",
}

# Mood (+1.0đ): trạng thái cảm xúc / nhu cầu chung
MOOD_TAGS = {
    "chill", "xả stress", "thư giãn", "lãng mạn", "sôi động",
    "vui vẻ", "khám phá", "cảm giác mạnh", "ăn uống", "hẹn hò",
    "gia đình", "bạn bè", "cặp đôi", "đi một mình", "giải trí",
    "vận động", "học hỏi", "sáng tạo",
}

# Map cách nói thông thường / teencode → group_type chuẩn trong DB
GROUP_TAG_MAP: Dict[str, str] = {
    "cặp đôi":   "Cặp đôi",      "đôi":       "Cặp đôi",
    "bồ":        "Cặp đôi",      "người yêu": "Cặp đôi",
    "hẹn hò":    "Cặp đôi",
    "gia đình":  "Gia đình",     "ba mẹ":     "Gia đình",
    "con cái":   "Gia đình",
    "bạn bè":    "Hội bạn",      "hội bạn":   "Hội bạn",
    "hội":       "Hội bạn",      "nhóm bạn":  "Hội bạn",
    "một mình":  "Đi một mình",  "solo":      "Đi một mình",
}

def parse_tags(nlp_tags: List[str]) -> Dict[str, List[str]]:
    """
    Phân loại NLP tags thành 2 nhóm điểm cho RecommenderEngine.

    Returns:
        {"style": [...], "mood": [...]}
        Tag không khớp STYLE_TAGS → đưa vào mood (vẫn có giá trị gợi ý).
    """
    style_list, mood_list = [], []
    for tag in nlp_tags:
        normalized = tag.lower().strip()
        if normalized in STYLE_TAGS:
            style_list.append(normalized)
        else:
            mood_list.append(normalized)
    return {"style": style_list, "mood": mood_list}


def parse_group_type(nlp_tags: List[str]) -> Optional[str]:
    """
    Tìm group type đầu tiên khớp trong NLP tags.
    VD: ["xả stress", "bồ", "chill"] → "Cặp đôi"
    Trả về None nếu không nhắc đến nhóm người.
    """
    for tag in nlp_tags:
        group = GROUP_TAG_MAP.get(tag.lower().strip())
        if group:
            return group
    return None
# ============================================================================

# ============================================================================
# SCORING ENGINE
# ============================================================================

class RecommenderEngine:
    """
    Thuật toán lọc và chấm điểm địa điểm theo 2 giai đoạn:
      1. Lọc cứng : loại địa điểm vi phạm ràng buộc bắt buộc
      2. Chấm điểm: rating gốc + tag match bonus − distance penalty
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {
            "weights": {
                "style":    2.0,    # +2.0đ mỗi style tag khớp
                "mood":     1.0,    # +1.0đ mỗi mood tag khớp
                "distance": -0.2,   # -0.2đ mỗi km xa hơn
            },
            "weather_rules": {
                "bad_weather_statuses":      ["RAIN", "STORM", "DRIZZLE"],
                "restricted_location_types": ["Outdoor"],
            },
            "max_results": 3,
        }

    # ── Haversine ────────────────────────────────────────────────────────────

    @staticmethod
    def _calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Tính khoảng cách đường chim bay (km) giữa 2 tọa độ GPS."""
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

    def _passes_hard_filter(
        self,
        loc: Dict,
        must_haves: Dict,
        current_time: float,
        weather: str,
    ) -> bool:
        """
        Trả về False nếu địa điểm vi phạm bất kỳ ràng buộc cứng nào.
        Thứ tự kiểm tra: giờ → ngân sách → thời tiết → loại hình → nhóm người.
        """
        # Giờ mở/đóng cửa
        if not (loc.get("open_time", 0) <= current_time <= loc.get("close_time", 24)):
            return False

        # Ngân sách
        if "budget" in must_haves and loc.get("price", 0) > must_haves["budget"]:
            return False

        # Thời tiết: loại outdoor khi trời xấu
        is_bad_weather     = weather in self.config["weather_rules"]["bad_weather_statuses"]
        is_restricted_type = loc.get("type") in self.config["weather_rules"]["restricted_location_types"]
        if is_bad_weather and is_restricted_type:
            return False

        # Loại hình cụ thể (nếu user yêu cầu rõ)
        if must_haves.get("category") and loc.get("category") != must_haves["category"]:
            return False

        # Rating tối thiểu
        if must_haves.get("min_rating") and loc.get("rating", 0) < must_haves["min_rating"]:
            return False

        # Nhóm người: kiểm tra group_type có trong tags của địa điểm không
        required_group = must_haves.get("group_type")
        if required_group:
            loc_tags_lower = [t.lower() for t in loc.get("tags", [])]
            if required_group.lower() not in loc_tags_lower:
                return False

        return True

    # ── Soft scoring ─────────────────────────────────────────────────────────

    def _score(
        self,
        loc: Dict,
        preferences: Dict[str, List[str]],
        user_coords: Tuple[float, float],
    ) -> Dict:
        """Chấm điểm 1 địa điểm: rating gốc + tag bonus − distance penalty."""
        score = loc.get("rating", 0.0)
        matched_styles, matched_moods = [], []

        for tag in loc.get("tags", []):
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
        """
        Pipeline lọc + chấm điểm → Top N địa điểm phù hợp nhất.

        Args:
            user_request:
                must_haves  : {"budget", "min_rating", "group_type", "category"}
                preferences : {"style": [...], "mood": [...]}  ← từ parse_tags()
            user_context:
                current_time : float hour (VD: 20.5)
                weather      : str (VD: "RAIN")
                coords       : (lat, lon)
            location_database:
                list[dict] chuẩn hoá từ get_all_places()

        Returns:
            list[dict] tối đa max_results phần tử, sắp xếp theo score giảm dần.
        """
        must_haves   = user_request.get("must_haves", {})
        preferences  = user_request.get("preferences", {})
        current_time = user_context["current_time"]
        weather      = user_context.get("weather", "CLEAR")
        user_coords  = user_context["coords"]

        # Giai đoạn 1: Lọc cứng
        valid = [
            loc for loc in location_database
            if self._passes_hard_filter(loc, must_haves, current_time, weather)
        ]

        # Giai đoạn 2: Chấm điểm
        scored = [self._score(loc, preferences, user_coords) for loc in valid]

        # Sắp xếp: score cao trước, cùng score thì gần hơn trước
        scored.sort(key=lambda x: (-x["total_score"], x["distance_km"]))

        return scored[: self.config["max_results"]]