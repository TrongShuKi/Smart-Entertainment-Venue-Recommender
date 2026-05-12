"""
firebase_config.py
==================
Khởi tạo Firebase Admin SDK và Firestore client.
Export 3 thứ để các file khác dùng:
    - db               : Firestore client (dùng để đọc/ghi dữ liệu)
    - FIREBASE_API_KEY : REST API key của Firebase (dùng trong auth_router)
    - GOOGLE_CONFIG    : Cấu hình Google OAuth (dùng trong auth_router)
"""

import os
import logging
from pathlib import Path

import toml
import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tìm file secrets.toml
# ---------------------------------------------------------------------------
def _find_secrets_path() -> Path:
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
# Khởi tạo Firebase Admin
# ---------------------------------------------------------------------------
def init_firebase_admin() -> None:
    if firebase_admin._apps:
        return 

    cred_dict = dict(_config["firebase_admin"])

    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    logger.info("[Firebase] Admin SDK đã khởi tạo thành công")


def get_firestore() -> firestore.Client:
    """Trả về Firestore client. Tự động gọi init nếu chưa sẵn sàng."""
    init_firebase_admin()
    return firestore.client()

db = get_firestore()