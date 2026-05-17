"""
history_service.py
==================
Quản lý lịch sử chat và gợi ý của người dùng trên Firestore.
Tách ra khỏi chat_router để router chỉ còn điều phối pipeline.

  - save_history() : Lưu 1 lượt gợi ý vào Firestore
  - get_history()  : Đọc N lượt gần nhất của một user
"""

import logging
from datetime import datetime
from typing import Dict, List

from backend.core.firebase_config import db as firestore_db

logger = logging.getLogger(__name__)

_COLLECTION_ROOT = "users"
_COLLECTION_HISTORY = "history"


def save_history(uid: str, query: str, full_response: dict) -> None:
    """
    Lưu 1 lượt gợi ý vào Firestore.
    Gọi bằng asyncio.to_thread() từ router để không block event loop.
    Không raise exception — lỗi lưu lịch sử không được ảnh hưởng response chính.

    Cấu trúc Firestore:
        users/{uid}/history/{auto_id}
            query     : str
            timestamp : str  (ISO 8601 UTC)
            results              : list[dict] (toàn bộ top_places)
            weather_info         : dict
            user_context_summary : str
    """
    try:
        ref = (
            firestore_db
            .collection(_COLLECTION_ROOT)
            .document(uid)
            .collection(_COLLECTION_HISTORY)
        )
        ref.add({
            "query":     query,
            "timestamp": datetime.utcnow().isoformat(),
            "results": full_response.get("top_places", []),
            "weather_info": full_response.get("weather_info"),
            "user_context_summary": full_response.get("user_context_summary")
        })
        logger.info(f"[History] Đã lưu lịch sử cho UID: {uid}")
    except Exception as exc:
        logger.warning(f"[History] Lỗi lưu Firestore (không ảnh hưởng response): {exc}")


def get_history(uid: str, limit: int = 5) -> List[Dict]:
    """
    Đọc N lượt gợi ý gần nhất của một user từ Firestore.
    Gọi bằng asyncio.to_thread() từ router.

    Returns:
        list[dict] sắp xếp mới nhất trước. [] nếu lỗi hoặc chưa có lịch sử.
    """
    try:
        query = (
            firestore_db
            .collection(_COLLECTION_ROOT)
            .document(uid)
            .collection(_COLLECTION_HISTORY)
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
        )
        docs = list(query.stream())
        return [doc.to_dict() for doc in docs]
    except Exception as exc:
        logger.error(f"[History] Lỗi đọc Firestore cho UID {uid}: {exc}")
        return []