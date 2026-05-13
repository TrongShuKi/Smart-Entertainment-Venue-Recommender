# 🌟 Smart Entertainment Venue Recommender

> Hệ thống gợi ý địa điểm vui chơi giải trí thông minh — dựa trên câu chat tự nhiên, thời tiết thực tế và vị trí người dùng.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.57-red?logo=streamlit)
![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-purple?logo=google)

---

## 📋 Mục lục

- [Tổng quan](#-tổng-quan)
- [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
- [Yêu cầu môi trường](#-yêu-cầu-môi-trường)
- [Cài đặt](#-cài-đặt)
- [Cấu hình .env](#-cấu-hình-env)
- [Cấu hình secrets.toml](#-cấu-hình-secretstoml)
- [Khởi tạo database](#-khởi-tạo-database)
- [Chạy ứng dụng](#-chạy-ứng-dụng)
- [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
- [API Reference](#-api-reference)

---

## 🎯 Tổng quan

Người dùng nhập câu chat tự nhiên như *"Muốn đi chill với bồ tối nay, tầm 200k, không ồn ào"* — hệ thống tự động:

1. **NLP** — Gemini phân tích câu chat, trích xuất ngân sách, tâm trạng, nhóm người, thời gian
2. **Weather** — Lấy thời tiết thực tế tại khu vực từ OpenWeatherMap
3. **Scoring** — Lọc cứng (giờ mở cửa, ngân sách, thời tiết) + chấm điểm mềm (tag match, khoảng cách)
4. **AI Generate** — Sinh mô tả + fact thú vị riêng cho từng địa điểm
5. **Response** — Trả Top 3 địa điểm kèm bản đồ Folium

---

## 🏗 Kiến trúc hệ thống

```
┌─────────────────────────────────────────────┐
│            Frontend (Streamlit)              │
│   app.py  ←→  api_client.py  ←→  map.py     │
└──────────────────┬──────────────────────────┘
                   │ HTTP REST
┌──────────────────▼──────────────────────────┐
│             Backend (FastAPI)                │
│                                             │
│  /auth/*          /suggest        /weather  │
│  auth_router  ←→  chat_router  ←→  weather  │
│       │               │            router   │
│  Firebase Auth    ai_service                │
│  (Login/Signup)   weather_service           │
│                   scoring_service           │
│                   history_service           │
└──────────┬────────────┬────────────────────┘
           │            │
    ┌──────▼──┐   ┌─────▼──────┐
    │Firestore│   │  SQLite DB │
    │(history)│   │ places.db  │
    └─────────┘   └────────────┘
```

---

## 🖥 Yêu cầu môi trường

| Công cụ | Phiên bản tối thiểu | Ghi chú                      |
|---------|---------------------|------------------------------|
| Python  | 3.11+               | Kiểm tra: `python --version` |
| pip     | 23+                 | Kiểm tra: `pip --version`    |

---

## 🚀 Cài đặt

### 1. Clone repo

```bash
git clone https://github.com/<your-org>/Smart-Entertainment-Venue-Recommender.git
cd Smart-Entertainment-Venue-Recommender
```

### 2. Tạo virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Cài dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Cấu hình .env

Tạo file `.env` tại **thư mục gốc** project (cùng cấp với `backend/`):

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Sau đó mở `.env` và điền các giá trị thực:

```dotenv
# ── Gemini AI ─────────────────────────────────────────────────────────────
# Lấy tại: https://aistudio.google.com/apikey
GEMINI_API_KEY=AIza...

# ── OpenWeatherMap ─────────────────────────────────────────────────────────
# Lấy tại: https://openweathermap.org/api → My API Keys
WEATHER_API_KEY=abc123...
WEATHER_API_TIMEOUT=10.0
WEATHER_CACHE_TTL=1800

# ── App ────────────────────────────────────────────────────────────────────
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
```

---

## 🔐 Cấu hình secrets.toml

File này chứa credentials Firebase — dùng cho Authentication và Firestore.

### Bước 1 — Tạo file

```bash
# Windows
mkdir .streamlit
copy .streamlit\secrets.toml.example .streamlit\secrets.toml

# macOS / Linux
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

### Bước 2 — Lấy Firebase credentials

1. Vào [Firebase Console](https://console.firebase.google.com) → chọn project
2. **Firebase Client API Key:**
   Project Settings → General → Web API Key → copy vào `[firebase_client].apiKey`
3. **Firebase Admin SDK:**
   Project Settings → Service Accounts → Generate new private key → tải file JSON
   Copy từng trường từ file JSON vào section `[firebase_admin]`
4. **Google OAuth** *(nếu dùng đăng nhập Google):*
   [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials → OAuth 2.0 Client IDs

### Bước 3 — Điền vào secrets.toml

```toml
# .streamlit/secrets.toml

[firebase_client]
apiKey = "AIza..."

[firebase_admin]
type = "service_account"
project_id = "your-project-id"
private_key_id = "abc123..."
private_key = "-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n"
client_email = "firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."

[google-login]
google-url = "https://accounts.google.com/o/oauth2/v2/auth"
google_client_id = "xxx.apps.googleusercontent.com"
google_client_secret = "GOCSPX-..."
google_redirect_uri = "http://localhost:8000/auth/google/callback"
frontend_url = "http://localhost:8501"
cookie_secure = false
```

---

## 🗄 Khởi tạo database

Chạy **một lần duy nhất** để convert file Excel sang SQLite:

```bash
# Đảm bảo file Excel đã có tại data/raw/location.xlsx
python -m data.database
```

Output thành công:

```
[INFO] Đọc Excel: .../data/raw/location.xlsx
[INFO] Số dòng gốc: 50
[SUCCESS] Đã import 50 địa điểm vào places.db
=== TOP 5 THEO RATING ===
 place_name          category  rating  price
 ...
[DONE] ETL hoàn tất.
```

> Chỉ cần chạy lại nếu bạn cập nhật file `location.xlsx`.

---

## ▶️ Chạy ứng dụng

Cần mở **2 terminal** chạy song song:

### Terminal 1 — Backend (FastAPI)

```bash
# Từ thư mục gốc project
uvicorn backend.main:app --reload --port 8000
```

Kiểm tra backend đang chạy: [http://localhost:8000/health](http://localhost:8000/health)

Swagger UI (test API): [http://localhost:8000/docs](http://localhost:8000/docs)

### Terminal 2 — Frontend (Streamlit)

```bash
# Từ thư mục gốc project
streamlit run frontend/app.py
```

Mở trình duyệt: [http://localhost:8501](http://localhost:8501)

---

## 📁 Cấu trúc thư mục

```
Smart-Entertainment-Venue-Recommender/
│
├── frontend/
│   ├── app.py                  # Giao diện chính Streamlit
│   ├── api_client.py           # HTTP client gọi Backend
│   └── components/
│       └── map.py              # Bản đồ Folium
│
├── backend/
│   ├── main.py                 # Khởi chạy FastAPI
│   ├── core/
│   │   ├── config.py           # Load biến môi trường từ .env
│   │   └── firebase_config.py  # Firebase Admin SDK + Firestore
│   ├── dependencies/
│   │   └── auth.py             # Xác thực Firebase JWT
│   ├── routers/
│   │   ├── chat_router.py      # POST /suggest — pipeline chính
│   │   ├── auth_router.py      # POST /auth/login, /signup, /google
│   │   └── weather_router.py   # GET /weather/current
│   ├── services/
│   │   ├── ai_service.py       # NLP + AI Generate (Gemini)
│   │   ├── weather_service.py  # OpenWeatherMap + JSON cache
│   │   ├── scoring_service.py  # Hard filter + Soft scoring
│   │   └── history_service.py  # Lịch sử tìm kiếm (Firestore)
│   └── schemas/
│       ├── request_schema.py
│       ├── response_schema.py
│       ├── ai_schema.py
│       └── auth_schema.py
│
├── data/
│   ├── raw/
│   │   └── location.xlsx       # File Excel 50 địa điểm (raw)
│   ├── database.py             # ETL Excel → SQLite + get_all_places()
│   ├── places.db               # SQLite (tự động tạo khi chạy ETL)
│   ├── weather_cache.json      # Cache thời tiết 30 phút (tự tạo)
│   └── ai_content_cache.json   # Cache AI generate vĩnh viễn (tự tạo)
│
├── .streamlit/
│   └── secrets.toml            # Firebase credentials
│
├── .env                        # API keys
├── .env.example                # Template .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 📡 API Reference

### POST `/suggest`
Gợi ý địa điểm từ câu chat.

```json
// Request body
{
  "query": "Muốn đi chill với bồ, tầm 200k, không ồn",
  "location": [10.7769, 106.7009]
}

// Headers (tuỳ chọn — bỏ qua để dùng Guest mode)
Authorization: Bearer <firebase_id_token>
```

```json
// Response 200
{
  "status": "success",
  "message": "Tìm thấy 3 địa điểm phù hợp!",
  "top_places": [
    {
      "id": "1",
      "name": "Đường sách Nguyễn Văn Bình",
      "category": "Văn hóa",
      "tag": "yên tĩnh",
      "price": 0,
      "rating": 4.7,
      "image_url": "https://...",
      "latitude": 10.779,
      "longitude": 106.700,
      "distance": 0.4,
      "description": "...",
      "fact": "..."
    }
  ],
  "weather_info": {
    "condition": "CLEAR",
    "condition_vi": "nắng đẹp",
    "temperature": 32.0,
    "rain_probability": 0.05,
    "source": "api"
  },
  "user_context_summary": "Chill · Cặp đôi · 200k"
}
```

### POST `/auth/login`
```json
// Request
{ "email": "user@example.com", "password": "••••••••" }

// Response
{ "email": "user@example.com", "uid": "...", "idToken": "eyJ..." }
```

### POST `/auth/signup`
```json
// Request
{ "email": "user@example.com", "password": "••••••••" }
```

### GET `/suggest/history?limit=5`
```
Headers: Authorization: Bearer <firebase_id_token>
```

### GET `/health`
```json
{ "status": "ok" }
```

---

## 🛠 Troubleshooting

| Lỗi | Nguyên nhân | Cách fix |
|-----|-------------|----------|
| `FileNotFoundError: raw/location.xlsx` | Chưa chạy ETL | `python -m data.database` |
| `401 Unauthorized` (Weather API) | Key chưa điền hoặc chưa activate | Đợi 30 phút sau khi đăng ký OWM |
| `429 RESOURCE_EXHAUSTED` (Gemini) | Hết quota free tier (20 req/ngày) | Đợi reset hàng ngày hoặc nâng cấp plan |
| `FileNotFoundError: secrets.toml` | Chưa tạo file cấu hình Firebase | Làm theo mục [Cấu hình secrets.toml](#-cấu-hình-secretstoml) |
| `Connect call failed 6379` | Redis không chạy | Bình thường — đã dùng JSON cache thay thế |

---

## 👥 Nhóm T04