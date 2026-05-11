"""
firebase_config.py
==================
Khởi tạo Firebase Admin SDK và Firestore client.
Export 3 thứ để các file khác dùng:
    - db               : Firestore client (dùng để đọc/ghi dữ liệu)
    - FIREBASE_API_KEY : REST API key của Firebase (dùng trong auth_router)
    - GOOGLE_CONFIG    : Cấu hình Google OAuth (dùng trong auth_router)

Cấu hình được đọc từ .streamlit/secrets.toml theo định dạng:
    [firebase_client]
    apiKey = "..."

    [firebase_admin]
    type = "service_account"
    project_id = "..."
    private_key = "..."
    client_email = "..."
    ...

    [google-login]
    google-url = "..."
    google_client_id = "..."
    google_client_secret = "..."
    google_redirect_uri = "..."
    frontend_url = "..."
    cookie_secure = false
"""

import os
import logging
from pathlib import Path

import toml
import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tìm file secrets.toml — thử nhiều đường dẫn để chạy được từ bất kỳ thư mục nào
# ---------------------------------------------------------------------------
def _find_secrets_path() -> Path:
    """
    Tìm .streamlit/secrets.toml tính từ thư mục gốc project (lên tối đa 3 cấp).
    Raise FileNotFoundError nếu không tìm thấy.
    """
    # Bắt đầu từ thư mục chứa file này, leo lên tìm
    current = Path(__file__).resolve().parent
    for _ in range(4):
        candidate = current / ".streamlit" / "secrets.toml"
        if candidate.exists():
            return candidate
        current = current.parent

    raise FileNotFoundError(
        "Không tìm thấy .streamlit/secrets.toml. "
        "Hãy tạo file này từ .streamlit/secrets.toml.example trước khi chạy."
    )


# ---------------------------------------------------------------------------
# Load config từ secrets.toml
# ---------------------------------------------------------------------------
_secrets_path = _find_secrets_path()
logger.info(f"[Firebase] Đọc secrets từ: {_secrets_path}")

with open(_secrets_path, "r", encoding="utf-8") as f:
    _config = toml.load(f)

# Export để auth_router dùng
FIREBASE_API_KEY: str = _config["firebase_client"]["apiKey"]
GOOGLE_CONFIG: dict   = _config["google-login"]


# ---------------------------------------------------------------------------
# Khởi tạo Firebase Admin (idempotent — chỉ init 1 lần dù import nhiều lần)
# ---------------------------------------------------------------------------
def init_firebase_admin() -> None:
    """
    Khởi tạo Firebase Admin SDK nếu chưa được khởi tạo.
    An toàn khi gọi nhiều lần — kiểm tra _apps trước khi init.
    """
    if firebase_admin._apps:
        return  # Đã init trước đó, bỏ qua

    cred_dict = dict(_config["firebase_admin"])

    # private_key trong TOML lưu ký tự "\n" dưới dạng string literal → cần unescape
    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    logger.info("[Firebase] Admin SDK đã khởi tạo thành công")


def get_firestore() -> firestore.Client:
    """Trả về Firestore client. Tự động gọi init nếu chưa sẵn sàng."""
    init_firebase_admin()
    return firestore.client()

db = get_firestore()