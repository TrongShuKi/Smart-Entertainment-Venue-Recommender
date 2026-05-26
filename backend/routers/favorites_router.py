"""
favorites_router.py
===================
CRUD yêu thích lưu trên Firestore.
Chỉ hoạt động khi đã đăng nhập (get_current_user).

Cấu trúc Firestore:
    users/{uid}/favorites/{place_id}
        (toàn bộ Place object)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel, Field
from typing import Optional

from backend.dependencies.auth import get_current_user
from backend.core.firebase_config import db as firestore_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/favorites", tags=["favorites"])

_COL_USERS = "users"
_COL_FAVS  = "favorites"


# ── Schema ──────────────────────────────────────────────────────────────────
class PlacePayload(BaseModel):
    """Khớp với Place schema từ response_schema.py"""
    id:          str
    name:        str
    category:    str   = ""
    tag:         str   = ""
    price:       int   = 0
    rating:      float = 0.0
    image_url:   str   = ""
    latitude:    float = 0.0
    longitude:   float = 0.0
    distance:    float = 0.0
    description: str   = ""
    fact:        str   = ""


# ── GET /favorites ───────────────────────────────────────────────────────────
@router.get("")
def get_favorites(user=Depends(get_current_user)):
    """Lấy toàn bộ danh sách yêu thích của user."""
    try:
        docs = (
            firestore_db
            .collection(_COL_USERS)
            .document(user["uid"])
            .collection(_COL_FAVS)
            .stream()
        )
        return {"favorites": [doc.to_dict() for doc in docs]}
    except Exception as e:
        logger.error(f"[Favorites] Lỗi GET cho UID {user['uid']}: {e}")
        raise HTTPException(status_code=500, detail="Không lấy được danh sách yêu thích")


# ── POST /favorites ──────────────────────────────────────────────────────────
@router.post("")
def add_favorite(place: PlacePayload, user=Depends(get_current_user)):
    """Thêm một địa điểm vào yêu thích. Dùng place.id làm document ID."""
    try:
        (
            firestore_db
            .collection(_COL_USERS)
            .document(user["uid"])
            .collection(_COL_FAVS)
            .document(str(place.id))
            .set(place.model_dump())
        )
        return {"message": f"Đã lưu '{place.name}'", "id": place.id}
    except Exception as e:
        logger.error(f"[Favorites] Lỗi POST cho UID {user['uid']}: {e}")
        raise HTTPException(status_code=500, detail="Không lưu được yêu thích")


# ── DELETE /favorites/{place_id} ─────────────────────────────────────────────
@router.delete("/{place_id}")
def remove_favorite(place_id: str, user=Depends(get_current_user)):
    """Xóa một địa điểm khỏi yêu thích."""
    try:
        (
            firestore_db
            .collection(_COL_USERS)
            .document(user["uid"])
            .collection(_COL_FAVS)
            .document(place_id)
            .delete()
        )
        return {"message": "Đã xóa", "id": place_id}
    except Exception as e:
        logger.error(f"[Favorites] Lỗi DELETE cho UID {user['uid']}: {e}")
        raise HTTPException(status_code=500, detail="Không xóa được yêu thích")