from fastapi import Header, HTTPException
from firebase_admin import auth as admin_auth
from typing import Optional
import backend.core.firebase_config 

def get_current_user(authorization: str = Header(...)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "").strip()

    try:
        decoded = admin_auth.verify_id_token(token)
        return {
            "uid": decoded.get("uid"),
            "email": decoded.get("email"),
            "token": token
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_optional_user(authorization: Optional[str] = Header(None)):
    """
    Dependency TÙY CHỌN: Dành riêng cho Guest Mode.
    Sử dụng cho API /suggest. Nếu có Token thì trả về user, nếu không thì trả về None.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None  # Trở thành Guest

    token = authorization.replace("Bearer ", "").strip()

    try:
        decoded = admin_auth.verify_id_token(token)
        return {
            "uid": decoded.get("uid"),
            "email": decoded.get("email"),
            "token": token
        }
    except Exception:
        return None