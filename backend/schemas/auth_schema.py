from pydantic import BaseModel, EmailStr

class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleLoginRequest(BaseModel):
    id_token: str

class AuthResponse(BaseModel):
    email: str
    uid: str
    idToken: str | None = None
    refreshToken: str | None = None