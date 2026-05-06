import requests

# Khai báo địa chỉ Backend FastAPI của bạn
API_BASE = "http://localhost:8000"

def signup(email: str, password: str):
    r = requests.post(f"{API_BASE}/auth/signup", json={
        "email": email,
        "password": password
    })
    r.raise_for_status()
    return r.json()

def login(email: str, password: str):
    r = requests.post(f"{API_BASE}/auth/login", json={
        "email": email,
        "password": password
    })
    r.raise_for_status()
    return r.json()

def google_login(id_token: str):
    r = requests.post(f"{API_BASE}/auth/google", json={
        "id_token": id_token
    })
    r.raise_for_status()
    return r.json()

def get_history(id_token: str, limit: int = 5):
    r = requests.get(
        f"{API_BASE}/suggest/history",
        params={"limit": limit},
        headers={"Authorization": f"Bearer {id_token}"}
    )
    r.raise_for_status()
    return r.json()

def get_suggestions(id_token: str, query: str, lat: float, lon: float):
    headers = {}
    if id_token:
        headers["Authorization"] = f"Bearer {id_token}"
        
    r = requests.post(
        f"{API_BASE}/suggest",
        json={
            "query": query,
            "location": [lat, lon]
        },
        headers=headers
    )
    r.raise_for_status()
    return r.json()