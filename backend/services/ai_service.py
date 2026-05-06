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
