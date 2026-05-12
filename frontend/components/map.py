import math
import folium
import streamlit as st
from streamlit_folium import st_folium


def calculate_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Tính khoảng cách đường chim bay (km) giữa 2 tọa độ GPS — Haversine."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


def render_map(
    user_coords: tuple[float, float],
    top_3_locations: list[dict],
) -> None:
    lat_u, lon_u = user_coords

    # ── Khởi tạo bản đồ ────────────────────────────────────────────────────
    m = folium.Map(
        location=[lat_u, lon_u],
        zoom_start=13,
        tiles="CartoDB dark_matter",   # dark tile mặc định
    )

    # ── Tile layers (người dùng có thể toggle) ──────────────────────────────
    folium.TileLayer("CartoDB positron",   name="🌞 Sáng").add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="🌙 Tối").add_to(m)
    folium.LayerControl(position="topright").add_to(m)

    folium.Marker(
        location=[lat_u, lon_u],
        popup=folium.Popup("<b>📍 Vị trí của bạn</b>", max_width=200),
        tooltip="Bạn đang ở đây",
        icon=folium.Icon(color="red", icon="user", prefix="fa"),
    ).add_to(m)

    # Vòng tròn bán kính 5 km (tham khảo)
    folium.Circle(
        location=[lat_u, lon_u],
        radius=5000,
        color="#ff4b4b",
        weight=1.5,
        fill=True,
        fill_opacity=0.04,
        tooltip="Bán kính 5 km",
    ).add_to(m)

    # ── Markers địa điểm gợi ý ─────────────────────────────────────────────
    RANK_COLORS  = ["orange", "blue", "green"]
    RANK_MEDALS  = ["🥇", "🥈", "🥉"]
    ICON_MAP = {
        "Bảo tàng":  "university",
        "Cafe":       "coffee",
        "Công viên":  "tree",
        "Giải trí":   "gamepad",
        "Nhà hàng":   "cutlery",
        "Bar":        "glass",
        "Spa":        "heart",
        "Rạp phim":   "film",
    }

    for i, place in enumerate(top_3_locations):
        lat_p, lon_p = place["coords"]
        distance     = calculate_haversine(lat_u, lon_u, lat_p, lon_p)
        fa_icon      = ICON_MAP.get(place.get("category", ""), "map-marker")
        color        = RANK_COLORS[i] if i < len(RANK_COLORS) else "cadetblue"
        medal        = RANK_MEDALS[i] if i < len(RANK_MEDALS) else f"#{i+1}"
        desc         = place.get("ai_description", "") or ""
        desc_short   = desc[:120] + "…" if len(desc) > 120 else desc

        popup_html = f"""
        <div style="width:240px; font-family:'Segoe UI',sans-serif;">
            <h4 style="margin:0 0 4px;color:#2E86C1;">{medal} {place['name']}</h4>
            <p style="margin:0;font-size:11px;color:#888;">
                📍 Cách bạn: <b>{distance} km</b> &nbsp;|&nbsp; {place.get('category','')}
            </p>
            <p style="font-size:12px;margin-top:6px;line-height:1.45;">{desc_short}</p>
        </div>
        """

        folium.Marker(
            location=[lat_p, lon_p],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{medal} {place['name']} ({distance} km)",
            icon=folium.Icon(color=color, icon=fa_icon, prefix="fa"),
        ).add_to(m)

        # Đường kết nối user → địa điểm
        folium.PolyLine(
            locations=[[lat_u, lon_u], [lat_p, lon_p]],
            color="#ff4b4b",
            weight=1.5,
            opacity=0.4,
            dash_array="6 8",
        ).add_to(m)

    # ── Render ─────────────────────────────────────────────────────────────
    st.markdown("### 🗺️ Bản đồ khu vực")
    st_folium(m, width="100%", height=460, returned_objects=[])