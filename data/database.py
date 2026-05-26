"""
database.py — fixed
====================
Exports:
    get_all_places() → list[dict]   ← được gọi bởi chat_router
    build_database()                ← chạy ETL Excel → SQLite (chỉ gọi 1 lần)
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

_DATA_DIR     = Path(__file__).resolve().parent
_EXCEL_FILE   = _DATA_DIR / "raw" / "location.xlsx"
_DB_FILE      = _DATA_DIR / "places.db"
_TABLE        = "places"


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _parse_time(value) -> float:
    """
    Chuyển chuỗi giờ bất kỳ → float hour.
    Hỗ trợ: "08:00", "08:00:00", "8", "08.00", None → 0.0
    """
    if value is None:
        return 0.0
    s = str(value).strip()
    if not s or s.lower() in ("none", "nan", "null"):
        return 0.0
    if ":" in s:
        parts = s.split(":")
        try:
            return float(parts[0]) + float(parts[1]) / 60
        except ValueError:
            return 0.0
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return 0.0


def _parse_tag_string(raw_str: str) -> List[str]:
    """
    Bóc tách 1 chuỗi tag (ngăn cách bởi dấu phẩy) thành list[str].
    """
    if not raw_str or str(raw_str).lower() in ("none", "nan", "null"):
        return []
    return [t.strip().lower() for t in str(raw_str).split(",") if t.strip()]


def _row_to_dict(row: sqlite3.Row) -> Dict:
    """
    Chuyển 1 sqlite3.Row → dict chuẩn hoá.
    """
    lat = row["latitude"]  or 0.0
    lon = row["longitude"] or 0.0

    raw_open  = _parse_time(row["open_time"])
    raw_close = _parse_time(row["close_time"])

    return {
        # ── Định danh ──────────────────────────────────────────────────
        "id":         str(row["id"]),
        "name":       str(row["place_name"] or "").strip(),

        # ── region để dùng cho text matching / hiển thị địa chỉ
        "region":     str(row["region"] or "").strip(),

        # ── Phân loại ──────────────────────────────────────────────────
        "category":   str(row["category"]   or "").strip(),
        # FIX CỰC MẠNH 1: Trả về đúng key 'space_type' cho Backend nhận diện
        "space_type": str(row["space_type"] or "").strip().lower(),

        # ── Giá & Rating ───────────────────────────────────────────────
        "price":      int(row["price"] or 0),
        "rating":     float(row["rating"] or 0.0),

        # ── Bản đồ ─────────────────────────────────────────────────────
        "coords":     (float(lat), float(lon)),

        # FIX CỰC MẠNH 2: Tách bạch rõ 2 mảng tags không gộp chung nữa
        "mood_tags":  _parse_tag_string(row["mood_tags"]),
        "group_tags": _parse_tag_string(row["group_tags"]),

        # ── Giờ mở/đóng cửa ────────────────────────────────────────────
        "open_time":  raw_open,
        "close_time": raw_close if raw_close > 0.0 else 24.0,

        # ── Ảnh ────────────────────────────────────────────────────────
        "image_url":  str(row["image_url"] or "").strip(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def get_all_places() -> List[Dict]:
    """
    Đọc toàn bộ địa điểm từ SQLite và trả về list[dict] chuẩn hoá.
    """
    if not _DB_FILE.exists():
        logger.error(
            f"[DB] Không tìm thấy places.db tại {_DB_FILE}. "
            "Hãy chạy: python -m data.database để tạo DB."
        )
        return []

    try:
        conn = sqlite3.connect(_DB_FILE)
        conn.row_factory = sqlite3.Row
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
# ETL: Excel → SQLite
# ══════════════════════════════════════════════════════════════════════════════

def build_database() -> None:
    """Pipeline ETL: đọc location.xlsx → làm sạch → ghi vào places.db."""
    import pandas as pd

    if not _EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file Excel tại: {_EXCEL_FILE}\n"
            "Hãy đặt file location.xlsx vào thư mục data/raw/"
        )

    print(f"[INFO] Đọc Excel: {_EXCEL_FILE}")
    df = pd.read_excel(_EXCEL_FILE, sheet_name="rawdata")
    df.columns = df.columns.str.strip() 
    print(f"[INFO] Số dòng gốc: {len(df)}")

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()

    # chuẩn hóa id số nguyên
    if "id" in df.columns:
        df["id"] = df["id"].astype(str).str.replace(r"\.0$", "", regex=True)

    # space_type viết thường
    if "space_type" in df.columns:
        df["space_type"] = df["space_type"].astype(str).str.lower().str.strip()

    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"].astype(str).str.replace(",", "."), errors="coerce").fillna(0.0)

    if "price" in df.columns:
        df["price"] = df["price"].replace({"free": "0", "Free": "0"})
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0).astype(int)

    if "coordinates" in df.columns:
        coords = df["coordinates"].str.split(",", expand=True)
        df["latitude"]  = pd.to_numeric(coords[0], errors="coerce")
        df["longitude"] = pd.to_numeric(coords[1], errors="coerce")

    print(f"[INFO] Ghi vào SQLite: {_DB_FILE}")
    conn = sqlite3.connect(_DB_FILE)
    df.to_sql(_TABLE, conn, if_exists="replace", index=False)
    conn.commit()

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


if __name__ == "__main__":
    build_database()