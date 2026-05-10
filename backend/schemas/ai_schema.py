"""
ai_schema.py
============
Tập trung toàn bộ Pydantic models dùng để ép Gemini trả về JSON chuẩn.

Có 2 schema:
  - NLPResponse          → dùng cho extract_nlp_intent()   (phân tích câu chat)
  - GeneratedPlaceContent → dùng cho generate_text()       (sinh mô tả + fact)
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ---------------------------------------------------------------------------
# SCHEMA 1: NLPResponse
# Mục đích: Ép Gemini nhả đúng 6 trường từ câu chat tự nhiên của người dùng.
# Dùng tại: ai_service.extract_nlp_intent()
# ---------------------------------------------------------------------------

class NLPResponse(BaseModel):
    location: Optional[str] = Field(
        default=None,
        description="Tên quận/huyện/khu vực cụ thể người dùng nhắc đến. Nếu không có để null."
    )
    max_price: Optional[int] = Field(
        default=None,
        description=(
            "Mức chi phí tối đa quy ra VNĐ (số nguyên). "
            "Tự quy đổi tiếng lóng: '1 lít'=100000, 'nửa củ'=500000, 'vài chục'=50000. "
            "Nếu không đề cập để null."
        )
    )
    tags: List[str] = Field(
        default_factory=list,
        description=(
            "Mảng các từ khóa mô tả nhu cầu: loại hình địa điểm, không khí, đi với ai, món ăn... "
            "Gom TẤT CẢ vào đây. "
            "Nếu khách nói KHÔNG thích gì đó, chuyển sang từ khóa TÍCH CỰC tương đương "
            "(vd: 'không ồn' → 'yên tĩnh', 'tránh đám đông' → 'vắng vẻ'). "
            "Tự hiểu teencode/không dấu: 'cf'='cà phê', 'q1'='Quận 1', 'đi vs bồ'='cặp đôi'."
        )
    )
    timeopen: Optional[bool] = Field(
        default=None,
        description=(
            "True nếu người dùng muốn lọc những chỗ ĐANG MỞ CỬA ngay bây giờ "
            "(vd: 'đang mở', 'bây giờ', 'lúc này'). Còn lại để null."
        )
    )
    min_rating: Optional[float] = Field(
        default=None,
        description=(
            "Số sao tối thiểu (float, thang 1.0–5.0). "
            "Tự suy luận nếu ngụ ý (vd: 'chỗ ngon', 'nổi tiếng' → 4.0; 'cực phẩm' → 4.5). "
            "Nếu không đề cập để null."
        )
    )
    current_time: Optional[str] = Field(
        default=None,
        description=(
            "Thời điểm người dùng muốn đến. Trả về chuỗi mô tả hoặc 'now' nếu đi ngay. "
            "Ví dụ: 'tối nay', 'sáng mai', 'cuối tuần', 'now'. "
            "Nếu không đề cập để null."
        )
    )


# ---------------------------------------------------------------------------
# SCHEMA 2: GeneratedPlaceContent
# Mục đích: Ép Gemini tách riêng description và fact thành 2 field,
#           thay vì trả về 1 chuỗi hỗn hợp khó parse.
# Dùng tại: ai_service.generate_text()
# ---------------------------------------------------------------------------

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
