import pandas as pd
import sqlite3
from pathlib import Path

# ======================================================
# CONFIG
# ======================================================
EXCEL_FILE = "raw/location.xlsx"
DATABASE_FILE = "hcmc_entertainment.db"
TABLE_NAME = "places"

# ======================================================
# CHECK FILE
# ======================================================
excel_path = Path(EXCEL_FILE)

if not excel_path.exists():
    raise FileNotFoundError(f"Không tìm thấy file Excel: {EXCEL_FILE}")

print("[INFO] Đang đọc file Excel...")

# ======================================================
# LOAD EXCEL
# ======================================================
df = pd.read_excel(EXCEL_FILE, sheet_name="Sheet1")

print("\n========== DATA PREVIEW ==========")
print(df.head())

print("\n========== DATA INFO ==========")
print(df.info())

# ======================================================
# DATA CLEANING
# ======================================================
print("\n[INFO] Đang làm sạch dữ liệu...")

# Xóa khoảng trắng dư
for col in df.columns:
    if df[col].dtype == "object":
        df[col] = df[col].astype(str).str.strip()

# Chuyển rating sang float
if "rating" in df.columns:
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

# Chuyển price
if "price" in df.columns:
    df["price"] = df["price"].replace("free", 0)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

# Tách latitude và longitude từ coordinates
if "coordinates" in df.columns:
    coords = df["coordinates"].str.split(",", expand=True)
    df["latitude"] = pd.to_numeric(coords[0], errors="coerce")
    df["longitude"] = pd.to_numeric(coords[1], errors="coerce")

# ======================================================
# CONNECT SQLITE DATABASE
# ======================================================
print("\n[INFO] Đang kết nối SQLite database...")

conn = sqlite3.connect(DATABASE_FILE)
cursor = conn.cursor()

# ======================================================
# CREATE TABLE
# ======================================================
create_table_query = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id INTEGER PRIMARY KEY,
    place_name TEXT,
    coordinates TEXT,
    latitude REAL,
    longitude REAL,
    price INTEGER,
    open_time TEXT,
    close_time TEXT,
    category TEXT,
    space_type TEXT,
    mood_tags TEXT,
    group_tags TEXT,
    rating REAL,
    image_url TEXT
)
"""

cursor.execute(create_table_query)
conn.commit()

print("[INFO] Đã tạo bảng thành công.")

# ======================================================
# EXPORT DATA TO SQLITE
# ======================================================
print("\n[INFO] Đang đưa dữ liệu vào database...")

# Ghi dữ liệu vào SQLite
df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)

print("[SUCCESS] Import dữ liệu thành công!")

# ======================================================
# TEST QUERY
# ======================================================
print("\n========== TOP 5 PLACES ==========")

query = f"""
SELECT place_name, category, rating, price
FROM {TABLE_NAME}
ORDER BY rating DESC
LIMIT 5
"""

result = pd.read_sql_query(query, conn)
print(result)

# ======================================================
# SAMPLE FILTER FUNCTION
# ======================================================
def recommend_places(
    max_price=200000,
    mood="chill",
    group_type="couple",
    min_rating=4.0
):
    sql = f"""
    SELECT *
    FROM {TABLE_NAME}
    WHERE price <= ?
    AND rating >= ?
    AND mood_tags LIKE ?
    AND group_tags LIKE ?
    ORDER BY rating DESC
    LIMIT 5
    """

    params = (
        max_price,
        min_rating,
        f"%{mood}%",
        f"%{group_type}%"
    )

    recommendations = pd.read_sql_query(sql, conn, params=params)

    return recommendations

# ======================================================
# DEMO RECOMMENDATION
# ======================================================
print("\n========== DEMO RECOMMENDATION ==========")

recommend_df = recommend_places(
    max_price=200000,
    mood="chill",
    group_type="couple"
)

print(recommend_df[[
    "place_name",
    "category",
    "price",
    "rating",
    "mood_tags"
]])

# ======================================================
# CLOSE DATABASE
# ======================================================
conn.close()

print("\n[INFO] Đã đóng kết nối database.")
print("[DONE] Hoàn tất pipeline Excel -> SQLite.")
