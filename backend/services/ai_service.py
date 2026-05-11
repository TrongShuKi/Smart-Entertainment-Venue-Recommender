"""
ai_service.py
=============
Hai hàm chính:
  - extract_nlp_intent(user_chat) → dict   # phân tích câu chat
  - generate_text(name, category, ctx)  → dict {"description": str, "fact": str}
"""

import os
import re
import logging
from typing import List, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()
logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")

# ── Fallback an toàn — LUÔN là dict ──────────────────────────────────────────
_FALLBACK_GENERATE = {"description": "", "fact": ""}
_FALLBACK_NLP = {
    "location": None, "max_price": None, "tags": [],
    "timeopen": None, "min_rating": None, "current_time": None,
}


# ══════════════════════════════════════════════════════════════════════════════
# SCHEMA cho generate_text — ép Gemini trả JSON 2 trường
# ══════════════════════════════════════════════════════════════════════════════
class GeneratedPlaceContent(BaseModel):
    description: str = Field(
        description=(
            "Đoạn mô tả ngắn gọn 1–2 câu về địa điểm, giọng văn khách quan và cuốn hút. "
            "KHÔNG xưng hô trực tiếp (không dùng: 'Bạn hãy', 'Chào bạn', 'Mời bạn'). "
            "Khéo léo lồng ghép ngữ cảnh của du khách nếu phù hợp."
        )
    )
    fact: str = Field(
        description=(
            "Một sự thật thú vị, độc đáo và ngắn gọn về địa điểm này. "
            "KHÔNG bắt đầu bằng '💡 Fact thú vị:' — chỉ trả về nội dung thuần túy."
        )
    )


# ══════════════════════════════════════════════════════════════════════════════
# SCHEMA cho extract_nlp_intent
# ══════════════════════════════════════════════════════════════════════════════
class NLPResponse(BaseModel):
    location:     Optional[str]   = Field(default=None, description="Tên quận/huyện/địa điểm. Nếu không có để null.")
    max_price:    Optional[int]   = Field(default=None, description="Mức giá tối đa quy ra VNĐ. Nếu không có để null.")
    tags:         List[str]       = Field(default_factory=list, description="Mảng từ khóa sở thích, không gian.")
    timeopen:     Optional[bool]  = Field(default=None, description="True nếu muốn chỗ đang mở cửa.")
    min_rating:   Optional[float] = Field(default=None, description="Số sao tối thiểu. Nếu không có để null.")
    current_time: Optional[str]   = Field(default=None, description="Thời gian đi chơi, 'now' nếu đi ngay.")


# ══════════════════════════════════════════════════════════════════════════════
# generate_text — LUÔN trả về dict {"description": str, "fact": str}
# ══════════════════════════════════════════════════════════════════════════════
def generate_text(location_name: str, category: str, user_context: str) -> dict:
    """
    Sinh mô tả + fact cho 1 địa điểm.

    Returns:
        {"description": str, "fact": str}
        Trả về dict rỗng-string nếu API lỗi — KHÔNG BAO GIỜ raise hoặc trả string thô.
    """
    try:
        client = genai.Client(api_key=API_KEY)

        prompt = (
            f"Địa điểm: '{location_name}' (Loại hình: {category}).\n"
            f"Ngữ cảnh du khách: {user_context}.\n\n"
            "Yêu cầu:\n"
            "1. Trường 'description': 1–2 câu mô tả cuốn hút, giọng khách quan, "
            "KHÔNG xưng hô trực tiếp. Lồng ghép ngữ cảnh du khách nếu tự nhiên.\n"
            "2. Trường 'fact': 1 sự thật thú vị, ngắn gọn, KHÔNG bắt đầu bằng '💡'."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeneratedPlaceContent,
                temperature=0.7,
            ),
        )

        # Dọn Markdown fence nếu có
        raw = response.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        validated = GeneratedPlaceContent.model_validate_json(raw)
        return validated.model_dump()   # {"description": "...", "fact": "..."}

    except Exception as e:
        logger.warning(f"[AI Generate] Lỗi cho '{location_name}': {e}")
        # Fallback có nội dung tối thiểu thay vì rỗng hoàn toàn
        return {
            "description": f"Một địa điểm {category} đáng trải nghiệm tại TP.HCM.",
            "fact": "Hãy đến tận nơi để cảm nhận không khí thực sự của địa điểm này.",
        }


# ══════════════════════════════════════════════════════════════════════════════
# extract_nlp_intent — trả về dict 6 trường chuẩn
# ══════════════════════════════════════════════════════════════════════════════
def extract_nlp_intent(user_chat: str) -> dict:
    try:
        client = genai.Client(api_key=API_KEY)

        system_instruction = """
        Bạn là hệ thống AI phân tích ngôn ngữ tự nhiên cho ứng dụng Smart Tourism.
        Nhiệm vụ: Trích xuất thông tin sang JSON THEO ĐÚNG CẤU TRÚC 6 TRƯỜNG ĐÃ QUY ĐỊNH.

        XỬ LÝ THÔNG MINH (KHÔNG ĐỔI CẤU TRÚC JSON):
        1. Lạc đề: Trả về JSON rỗng nếu câu KHÔNG liên quan du lịch/ăn uống/vui chơi.
        2. Đổi ý: Lấy giá trị ĐƯỢC CHỐT CUỐI CÙNG.
        3. Tiền lóng: Tự quy đổi ("nửa củ"=500000, "1 lít"=100000, "vài chục"=50000).
        4. Teencode & không dấu: Tự hiểu (q1, cf, ko ồn, đi vs bồ).
        5. Từ khóa: Gom TẤT CẢ nhu cầu vào `tags`. Từ phủ định → từ tích cực tương đương.
        """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f'Câu chat người dùng: "{user_chat}"',
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=NLPResponse,
                temperature=0.0,
            ),
        )

        raw = response.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        validated = NLPResponse.model_validate_json(raw)
        return validated.model_dump()

    except Exception as e:
        logger.error(f"[NLP] Lỗi trích xuất: {e}")
        return _FALLBACK_NLP.copy()