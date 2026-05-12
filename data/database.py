"""
database.py
===========
Module quản lý dữ liệu địa điểm từ SQLite.

Exports:
    get_all_places() → list[dict]   ← được gọi bởi chat_router
    build_database()                ← chạy ETL Excel → SQLite (chỉ gọi 1 lần)

Cách chạy ETL lần đầu (từ thư mục gốc project):
    python -m data.database
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

# ── Đường dẫn tuyệt đối — không phụ thuộc vào CWD ──────────────────────────
_DATA_DIR     = Path(__file__).resolve().parent          # .../data/
_EXCEL_FILE   = _DATA_DIR / "raw" / "location.xlsx"
_DB_FILE      = _DATA_DIR / "places.db"
_TABLE        = "places"


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS — parse dữ liệu thô từ DB
# ══════════════════════════════════════════════════════════════════════════════

def _parse_time(value) -> float:
    """
    Chuyển chuỗi giờ bất kỳ → float hour.
    Hỗ trợ: "08:00", "8:00", "8", "08.00", None → 0.0
    """
    if value is None:
        return 0.0
    s = str(value).strip()
    if not s or s.lower() in ("none", "nan", "null"):
        return 0.0
    # Dạng "HH:MM" hoặc "H:MM"
    if ":" in s:
        parts = s.split(":")
        try:
            return float(parts[0]) + float(parts[1]) / 60
        except ValueError:
            return 0.0
    # Dạng số thuần
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return 0.0


def _parse_tags(raw_mood: str, raw_group: str) -> List[str]:
    """
    Ghép mood_tags + group_tags (chuỗi phân cách bằng dấu phẩy) → list[str] đã strip + lower.
    """
    tags: List[str] = []
    for raw in (raw_mood, raw_group):
        if not raw or str(raw).lower() in ("none", "nan", "null"):
            continue
        for t in str(raw).split(","):
            t = t.strip().lower()
            if t:
                tags.append(t)
    return tags


def _row_to_dict(row: sqlite3.Row) -> Dict:
    """
    Chuyển 1 sqlite3.Row → dict chuẩn mà scoring_service.py mong đợi.
    """
    lat  = row["latitude"]  or 0.0
    lon  = row["longitude"] or 0.0
    return {
        # ── Định danh ──────────────────────────────────────────────────
        "id":         str(row["id"]),
        "name":       str(row["place_name"] or "").strip(),

        # ── Phân loại ──────────────────────────────────────────────────
        "category":   str(row["category"]   or "").strip(),
        "type":       str(row["space_type"] or "").strip(),   # "Indoor" | "Outdoor"

        # ── Giá & Rating ───────────────────────────────────────────────
        "price":      int(row["price"] or 0),
        "rating":     float(row["rating"] or 0.0),

        # ── Bản đồ ─────────────────────────────────────────────────────
        "coords":     (float(lat), float(lon)),

        # ── Tags (scoring dùng để match) ───────────────────────────────
        "tags":       _parse_tags(row["mood_tags"], row["group_tags"]),

        # ── Giờ mở/đóng cửa (float hour, vd: 8.5 = 08:30) ─────────────
        "open_time":  _parse_time(row["open_time"]),
        "close_time": _parse_time(row["close_time"]),

        # ── Ảnh ────────────────────────────────────────────────────────
        "image_url":  str(row["image_url"] or "").strip(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def get_all_places() -> List[Dict]:
    """
    Đọc toàn bộ địa điểm từ SQLite và trả về list[dict] chuẩn hoá.
    Được gọi bởi chat_router mỗi lần có request.

    Returns:
        list[dict] — rỗng nếu DB chưa tồn tại hoặc lỗi đọc.
    """
    if not _DB_FILE.exists():
        logger.error(
            f"[DB] Không tìm thấy places.db tại {_DB_FILE}. "
            "Hãy chạy: python -m data.database để tạo DB."
        )
        return []

    try:
        conn = sqlite3.connect(_DB_FILE)
        conn.row_factory = sqlite3.Row          # truy cập theo tên cột
        cur  = conn.cursor()
        cur.execute(f"SELECT * FROM {_TABLE}")
        rows = cur.fetchall()
        conn.close()

        places = [_row_to_dict(r) for r in rows]
        logger.info(f"[DB] Đã load {len(places)} địa điểm từ SQLite.")
        return places

    except Exception as exc:
        logger.error(f"[DB] Lỗi đọc SQLite: {exc}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
# ETL: Excel → SQLite  (chỉ chạy khi gọi trực tiếp)
# ══════════════════════════════════════════════════════════════════════════════

def build_database() -> None:
    """
    Pipeline ETL: đọc location.xlsx → làm sạch → ghi vào places.db.
    Gọi hàm này 1 lần duy nhất để khởi tạo DB, sau đó dùng get_all_places().
    """
    import pandas as pd

    # ── Kiểm tra file nguồn ─────────────────────────────────────────────────
    if not _EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file Excel tại: {_EXCEL_FILE}\n"
            "Hãy đặt file location.xlsx vào thư mục data/raw/"
        )

    print(f"[INFO] Đọc Excel: {_EXCEL_FILE}")
    df = pd.read_excel(_EXCEL_FILE, sheet_name="Sheet1")

    print(f"[INFO] Số dòng gốc: {len(df)}")
    print(df.head(3))

    # ── Làm sạch ────────────────────────────────────────────────────────────
    print("[INFO] Làm sạch dữ liệu...")

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()

    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)

    if "price" in df.columns:
        df["price"] = df["price"].replace({"free": "0", "Free": "0"})
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).astype(int)

    if "coordinates" in df.columns:
        coords = df["coordinates"].str.split(",", expand=True)
        df["latitude"]  = pd.to_numeric(coords[0], errors="coerce")
        df["longitude"] = pd.to_numeric(coords[1], errors="coerce")

    # ── Ghi vào SQLite ───────────────────────────────────────────────────────
    print(f"[INFO] Ghi vào SQLite: {_DB_FILE}")
    conn = sqlite3.connect(_DB_FILE)

    df.to_sql(_TABLE, conn, if_exists="replace", index=True, index_label="id")
    conn.commit()

    # ── Verify ───────────────────────────────────────────────────────────────
    count = conn.execute(f"SELECT COUNT(*) FROM {_TABLE}").fetchone()[0]
    print(f"[SUCCESS] Đã import {count} địa điểm vào places.db")

    top5 = pd.read_sql_query(
        f"SELECT place_name, category, rating, price FROM {_TABLE} ORDER BY rating DESC LIMIT 5",
        conn,
    )
    print("\n=== TOP 5 THEO RATING ===")
    print(top5.to_string(index=False))

    conn.close()
    print("[DONE] ETL hoàn tất.")


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    build_database()