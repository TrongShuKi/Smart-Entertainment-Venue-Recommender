from google import genai
from google.genai import types

from pydantic import BaseModel, Field
from typing import List, Optional
import json
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

#  Hàm Trích xuất NLP

def generate_text(location_name, category, user_context):
    """
    Hàm tạo sinh nội dung văn hóa và fact thú vị cho địa điểm.
    """
    try:
        client = genai.Client(api_key=API_KEY)
        
        prompt = f"""
        Viết 1 đoạn tóm tắt ngắn gọn (khoảng 2 câu) để hiển thị trên thẻ website du lịch cho địa điểm: '{location_name}' (Loại hình: {category}).
        Ngữ cảnh của du khách: {user_context}.

        YÊU CẦU NGHIÊM NGẶT:
        1. Giọng văn khách quan, hiện đại và cuốn hút. 
        2. KHÔNG xưng hô trò chuyện trực tiếp (TUYỆT ĐỐI KHÔNG dùng các cụm từ như: "Chào bạn", "Mời hai bạn", "Chúng ta cùng", "Bạn hãy").
        3. Khéo léo chọn góc nhìn phù hợp với ngữ cảnh của khách nhưng không được gượng ép. (Ví dụ: Nếu khách đi cặp đôi đến nơi lịch sử, hãy nhấn mạnh không gian kiến trúc ấn tượng hoặc sự yên tĩnh để đi dạo cùng nhau, đừng dạy triết lý).
        4. Cuối cùng đưa ra một "💡 Fact thú vị: " là một sự thật ngắn gọn về nơi này.
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    
    except Exception as e:
        print(f"Lỗi AI Generate: {e}")
        return f"Một địa điểm tuyệt vời thuộc loại hình {category} đang chờ bạn khám phá! 💡 Fact thú vị: Hãy đến tận nơi để trải nghiệm nhé!"

# HÀM TRÍCH XUẤT NLP 
class NLPResponse(BaseModel):
    location: Optional[str] = Field(description="Tên quận/huyện/địa điểm. Nếu không có để null.")
    max_price: Optional[int] = Field(description="Mức giá tối đa quy ra VNĐ (vd: 100k -> 100000). Nếu không có để null.")
    tags: List[str] = Field(description="Mảng các từ khóa sở thích, không gian (vd: 'yên tĩnh', 'cà phê').")
    timeopen: Optional[bool] = Field(description="Trả về true nếu muốn chỗ 'đang mở cửa', 'bây giờ'. Nếu không để null.")
    min_rating: Optional[float] = Field(description="Số sao tối thiểu (vd: 4.0). Nếu không có để null.")
    current_time: Optional[str] = Field(description="Thời gian đi chơi (vd: 'tối nay'). Đi ngay trả về 'now'. Nếu không để null.")

def extract_nlp_intent(user_chat: str) -> dict:
    try:
        client = genai.Client(api_key=API_KEY)
        
        system_instruction = """
        Bạn là hệ thống AI phân tích ngôn ngữ tự nhiên.
        Nhiệm vụ: Phân tích câu nói của người dùng và trích xuất thông tin chuẩn xác theo định dạng JSON.
        Lưu ý: Quy đổi tiền tệ tiếng lóng thành số nguyên VNĐ.
        """
        
        prompt = f'Ngữ cảnh người dùng: "{user_chat}"'
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=NLPResponse,
                temperature=0.0, 
            ),
        )
        
        return json.loads(response.text)

    except Exception as e:
        print(f"Lỗi khi trích xuất NLP: {e}")
        return {
            "location": None, "max_price": None, "tags": [], 
            "timeopen": None, "min_rating": None, "current_time": None
        }
