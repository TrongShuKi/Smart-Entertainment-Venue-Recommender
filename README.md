# 🌍 Smart Tourism System (Hệ thống Du lịch Thông minh)

Chào mừng anh em đến với Đồ án môn Tư duy Tính toán! Đây là kho chứa mã nguồn chính thức của nhóm. 
Hệ thống sử dụng kiến trúc Client-Server: Giao diện web chạy bằng **Streamlit** (Frontend) và Máy chủ xử lý API chạy bằng **FastAPI** (Backend).

---

## 🚀 1. Yêu cầu hệ thống (Prerequisites)
Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt:
- **Python** (phiên bản 3.9 trở lên).
- **Git**.
---

## ⚙️ 2. Hướng dẫn Cài đặt & Setup lần đầu

**Bước 1: Tải mã nguồn về máy**
Mở Terminal / Git Bash và gõ lệnh:
```bash
git clone <link-github-của-repo-nhóm>
```

**Bước 2: Cài đặt các thư viện cần thiết**
```bash
pip install -r requirements.txt
```

**Bước 3: Thiết lập file bảo mật (Keys & Configs)**
Hệ thống cần các API Key để hoạt động (Gemini, Firebase). 
> ⚠️ **LƯU Ý:** Tuyệt đối KHÔNG đẩy các file này lên Github. Đã được chặn sẵn trong `.gitignore`.
1. Tự tạo hoặc xin nội dung file `.env` và thư mục `.streamlit/secrets.toml`.
2. Tạo file `.env` ở thư mục gốc (ngang hàng với README.md) và dán nội dung vào.
3. Tạo thư mục `.streamlit` ở thư mục gốc, bên trong tạo file `secrets.toml` và dán cấu hình Firebase vào.

---

## 🏃 3. Hướng dẫn Khởi chạy Hệ thống

Để hệ thống hoạt động, chúng ta cần bật cả Backend và Frontend song song. **Hãy mở 2 cửa sổ Terminal khác nhau (đảm bảo cả 2 đều đã activate `venv`).**

**Terminal 1: Khởi động Backend (FastAPI)**
```bash
uvicorn backend.main:app --reload --port 8000
```
✅ *Thành công khi thấy dòng chữ:* `Application startup complete.` (API đang chạy ở `http://localhost:8000`).

**Terminal 2: Khởi động Frontend (Streamlit)**
```bash
streamlit run frontend/app.py
```
✅ *Thành công:* Trình duyệt sẽ tự động mở trang web giao diện chính ở `http://localhost:8501`. Thử nhập một câu tâm tư và bấm nút "Gợi ý" để test kết nối!

---

## 🛠️ 4. Quy trình làm việc nhóm (Git Workflow)

Để tránh xung đột (conflict) làm sập hệ thống, **mọi người TUYỆT ĐỐI tuân thủ quy tắc sau:**
1. **KHÔNG** code trực tiếp hay đẩy thẳng (push) lên nhánh `main` hoặc `dev`.
2. **Luôn xuất phát từ nhánh `dev` mới nhất:**
   ```bash
   git checkout dev
   git pull origin dev
   ```
3. **Tạo nhánh riêng cho công việc của mình:**
   
```bash
   git checkout -b ten-nhanh-cua-ban 
   # Ví dụ: git checkout -b feat-weather-api
   ```
4. **Code, Lưu và Đẩy nhánh cá nhân lên Github:**
   ```bash
   git add .
   git commit -m "Mô tả tính năng vừa làm"
   git push origin ten-nhanh-cua-ban
   ```
5. **Tạo Pull Request (PR):** Lên Github, tạo PR xin gộp nhánh của bạn vào `dev` và nhắn Team Lead vào duyệt (Review code).

---

## 📁 5. Cấu trúc thư mục để làm việc
Mọi người làm nhiệm vụ nào thì vào đúng thư mục đó code, tránh sửa nhầm file của nhau:
- Nhóm Frontend (Giao diện, Bản đồ): Code trong thư mục `frontend/`.
- Nhóm API Thời tiết: Code file `backend/services/weather_service.py` và `backend/routers/weather_router.py`.
- Nhóm AI (Xử lý NLP): Code file `backend/services/ai_service.py`.
- Nhóm Thuật toán (Scoring): Code file `backend/services/scoring_service.py`.
- Nhóm Data: Đặt dữ liệu Excel vào `data/raw/` và code tiền xử lý ở `data/database.py`.