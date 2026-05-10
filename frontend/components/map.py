import math
import folium
import streamlit as st
from streamlit_folium import st_folium

def calculate_haversine(lat1, lon1, lat2, lon2):
    """
    Thuật toán tính khoảng cách đường chim bay (km) giữa 2 tọa độ GPS.
    """
    R = 6371.0
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return round(distance, 1) # Làm tròn 1 chữ số thập phân

def render_map(user_coords, top_3_locations):
    """
    Hàm vẽ bản đồ và render lên Streamlit.
    user_coords: tuple (vĩ độ, kinh độ)
    top_3_locations: list các dictionary chứa thông tin địa điểm
    """
    # 1. Khởi tạo bản đồ, lấy tâm là vị trí người dùng, zoom level 13
    m = folium.Map(location=[user_coords[0], user_coords[1]], zoom_start=13)
    
    # 2. Thả Marker cho Người dùng (Màu đỏ, icon người)
    folium.Marker(
        location=[user_coords[0], user_coords[1]],
        popup="<b>Vị trí của bạn</b>",
        tooltip="Bạn đang ở đây",
        icon=folium.Icon(color="red", icon="user", prefix='fa')
    ).add_to(m)
    
    # 3. Duyệt qua mảng Top 3 để thả Marker
    for i, place in enumerate(top_3_locations):
        lat, lon = place['coords']
        
        # Gọi hàm tính khoảng cách
        distance = calculate_haversine(user_coords[0], user_coords[1], lat, lon)
        
        # Mapping Icon cho đẹp mắt
        icon_dict = {"Bảo tàng": "university", "Cafe": "coffee", "Công viên": "tree", "Giải trí": "gamepad"}
        fa_icon = icon_dict.get(place['category'], "info-sign") # Default icon
        
        popup_html = f"""
        <div style="width: 250px;">
            <h4 style="margin-bottom: 5px; color: #2E86C1;">#{i+1} {place['name']}</h4>
            <p style="margin-top: 0px; font-size: 12px; color: gray;">
                📍 Cách bạn: <b>{distance} km</b>
            </p>
            <p style="font-size: 13px;">{place['ai_description']}</p>
        </div>
        """
        
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"Nhấn để xem {place['name']}",
            icon=folium.Icon(color="blue", icon=fa_icon, prefix='fa')
        ).add_to(m)

    # 4. Hiển thị bản đồ lên Streamlit
    st.markdown("### 🗺️ Bản đồ khu vực")
    st_data = st_folium(m, width=700, height=500)
    return st_data
