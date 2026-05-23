from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.auth_router import router as auth_router
from backend.routers.chat_router import router as suggest_router
from backend.routers.weather_router import router as weather_router
from backend.routers.favorites_router import router as favorites_router

app = FastAPI(title="Smart Suggestion API", version="1.0.0")

# Cấu hình CORS để cho phép Frontend (Streamlit) giao tiếp với Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(suggest_router)
app.include_router(weather_router, prefix="/weather", tags=["weather"])
app.include_router(favorites_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart Suggestion API"}

@app.get("/health")
def health():
    return {"status": "ok"}