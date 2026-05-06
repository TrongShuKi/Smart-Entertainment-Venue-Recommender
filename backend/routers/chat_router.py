from fastapi import APIRouter, Depends
from typing import Optional

from backend.schemas.request_schema import SuggestionRequest
from backend.schemas.response_schema import SuggestionResponse, Place
from backend.dependencies.auth import get_optional_user

router = APIRouter(prefix="/suggest", tags=["Suggest"])

@router.post("", response_model=SuggestionResponse)
def get_suggestions(
    payload: SuggestionRequest, 
    user: Optional[dict] = Depends(get_optional_user) # Chỗ này dùng hàm auth của bạn
):
    # Log để kiểm tra user đang là Khách hay đã đăng nhập
    if user:
        print(f"Người dùng đang gọi API: {user.get('email')}")
    else:
        print("Khách vãng lai (Guest) đang gọi API")
        
    print(f"Câu hỏi: {payload.query}")
    print(f"Vị trí: {payload.location}")

    # TODO: Gọi AI Service và Scoring Service ở đây
    # Tạm thời trả về dữ liệu mẫu để API chạy được
    
    fake_places = [
        Place(
            id="D01", 
            name="Thảo Cầm Viên", 
            tag="Sôi động", 
            distance=2.5, 
            description="Nơi bảo tồn động thực vật lâu đời.", 
            fact="Có hơn 1000 cá thể động vật!"
        )
    ]

    return SuggestionResponse(
        status="success",
        message="Đã nhận yêu cầu thành công!",
        top_places=fake_places
    )

@router.get("/history")
def get_history(limit: int = 5, user: dict = Depends(get_optional_user)):
    # Phải có User mới xem được lịch sử
    if not user:
        return {"message": "Vui lòng đăng nhập để xem lịch sử", "history": []}
    
    return {"message": f"Lịch sử của {user.get('email')}", "history": ["(Lịch sử mẫu)"]}