import secrets
from urllib.parse import urlencode
import requests
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from firebase_admin import auth as admin_auth

from backend.schemas.auth_schema import SignupRequest, LoginRequest, GoogleLoginRequest
from backend.dependencies.auth import get_current_user
from backend.core.firebase_config import FIREBASE_API_KEY, GOOGLE_CONFIG

router = APIRouter(prefix="/auth", tags=["auth"])

# Biến cấu hình Google
GOOGLE_URL = GOOGLE_CONFIG["google-url"]
GOOGLE_CLIENT_ID = GOOGLE_CONFIG["google_client_id"]
GOOGLE_CLIENT_SECRET = GOOGLE_CONFIG["google_client_secret"]
GOOGLE_REDIRECT_URI = GOOGLE_CONFIG["google_redirect_uri"]
FRONTEND_URL = GOOGLE_CONFIG["frontend_url"]
COOKIE_SECURE = GOOGLE_CONFIG.get("cookie_secure", False)

@router.post("/signup")
def signup(payload: SignupRequest):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"email": payload.email, "password": payload.password, "returnSecureToken": True})
    if res.status_code != 200:
        raise HTTPException(status_code=400, detail=res.json())
    return {"message": "Tạo tài khoản thành công"}

@router.post("/login")
def login(payload: LoginRequest):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    res = requests.post(url, json={"email": payload.email, "password": payload.password, "returnSecureToken": True})
    if res.status_code != 200:
        raise HTTPException(status_code=401, detail="Sai email hoặc mật khẩu")
    
    data = res.json()
    return {
        "email": payload.email,
        "uid": data["localId"],
        "idToken": data["idToken"],
        "refreshToken": data.get("refreshToken")
    }

@router.post("/google")
def google_login(payload: GoogleLoginRequest):
    try:
        decoded = admin_auth.verify_id_token(payload.id_token)
        return {
            "email": decoded.get("email"),
            "uid": decoded.get("uid"),
            "idToken": payload.id_token
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Google token invalid: {e}")

@router.get("/google/start")
def google_start():
    state = secrets.token_urlsafe(32)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

    response = RedirectResponse(url=google_auth_url, status_code=302)
    response.set_cookie(
        key="google_oauth_state", value=state, max_age=600,
        httponly=True, secure=COOKIE_SECURE, samesite="lax", path="/"
    )
    return response

@router.get("/google/callback")
def google_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    saved_state = request.cookies.get("google_oauth_state")
    if not saved_state or not state or saved_state != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code, "client_id": GOOGLE_CLIENT_ID, "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI, "grant_type": "authorization_code",
        }, timeout=20
    )
    if not token_resp.ok:
        raise HTTPException(status_code=400, detail="Failed to exchange Google code")

    google_id_token = token_resp.json().get("id_token")

    firebase_resp = requests.post(
        f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_API_KEY}",
        json={
            "postBody": urlencode({"id_token": google_id_token, "providerId": "google.com"}),
            "requestUri": GOOGLE_REDIRECT_URI, "returnIdpCredential": True, "returnSecureToken": True,
        }, timeout=20
    )
    if not firebase_resp.ok:
        raise HTTPException(status_code=400, detail="Failed to sign in with Firebase Google provider")

    firebase_id_token = firebase_resp.json().get("idToken")
    separator = "&" if "?" in FRONTEND_URL else "?"
    redirect_to_frontend = f"{FRONTEND_URL}{separator}{urlencode({'id_token': firebase_id_token})}"

    response = RedirectResponse(url=redirect_to_frontend, status_code=302)
    response.delete_cookie("google_oauth_state", path="/")
    return response

@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"email": user["email"], "uid": user["uid"]}