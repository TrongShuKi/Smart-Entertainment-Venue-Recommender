import streamlit as st
import pandas as pd
import pydeck as pdk
import time

# Cấu hình trang
st.set_page_config(page_title="Smart Suggestion System", layout="wide", page_icon="🌟")

# Khởi tạo State
if 'lang' not in st.session_state:
    st.session_state.lang = 'vi'
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'

# Hàm xử lý theme
def apply_theme(theme):
    if theme == 'light':
        st.markdown("""
            <style>
            .stApp { background-color: #ffffff; color: #31333F; }
            [data-testid="stHeader"] { background-color: #ffffff; }
            .stMarkdown, p, h1, h2, h3, h4, h5, h6 { color: #31333F !important; }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            .stApp { background-color: #0e1117; color: #ffffff; }
            [data-testid="stHeader"] { background-color: #0e1117; }
            </style>
        """, unsafe_allow_html=True)

apply_theme(st.session_state.theme)

# Ngôn ngữ
text = {
    'vi': {
        'title': " ENTERTAINMENT",
        'sub': "Gợi ý điểm vui chơi",
        'input_header': "####  Hôm nay bạn muốn trải nghiệm điều gì?",
        'input_label': "Chia sẻ tâm tư của bạn tại đây nhé...",
        'input_placeholder': "Ví dụ: Muốn đi chill với bồ, tầm 500k...",
        'btn_send': " Gửi tâm tư",
        'loading': " AI đang phân tích dữ liệu...",
        'about': "Thông tin nhóm",
        'suggest_title': " Gợi Ý Dành Riêng Cho Bạn",
        'price': "Giá",
        'detail': "Chi tiết",
        'team_info': "Nhóm T04", 
        'lang_sel': "Ngôn ngữ",
        'theme_sel': "Giao diện",
        'settings': "Cài đặt hệ thống"
    },
    'en': {
        'title': " ENTERTAINMENT",
        'sub': "Suggest entertainment place",
        'input_header': "####  What's on your mind today?",
        'input_label': "Share your thoughts with us...",
        'input_placeholder': "Ex: Chill place for couple, budget 500k...",
        'btn_send': " Send request",
        'loading': " AI is processing...",
        'about': "About Us",
        'suggest_title': " Perfect Matches For You",
        'price': "Price",
        'detail': "Detail",
        'team_info': "Group T04", 
        'lang_sel': "Language",
        'theme_sel': "Theme",
        'settings': "System Settings"
    }
}

L = text[st.session_state.lang]

# Tinh chỉnh CSS
st.markdown("""
    <style>
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        transition: all 0.4s ease; 
        border: 1px solid #ff4b4b; 
        color: #ff4b4b;
        background: transparent;
    }
    .stButton>button:hover { 
        background: linear-gradient(45deg, #ff4b4b, #ff8080);
        color: white; 
        /* Bỏ hiệu ứng nổi và phóng to lúc di chuột vào */
        /* transform: scale(1.02); */
        /* box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4); */
    }

    div[data-testid="stVerticalBlock"] > div:has(div.stImage) {
        transition: all 0.3s ease;
        border-radius: 15px;
    }
    div[data-testid="stColumn"]:last-child {
        display: flex;
        justify-content: flex-end;
    }
    </style>
    """, unsafe_allow_html=True)

# Thanh điều hướng
nav_col, setting_col = st.columns([4, 1])

with setting_col:
    with st.popover("⚙️ " + L['settings']):
        st.write(f"**{L['theme_sel']}**")
        theme_choice = st.radio("Theme", ["Dark", "Light"], 
                                index=0 if st.session_state.theme == 'dark' else 1,
                                label_visibility="collapsed")
        st.divider()
        st.write(f"**{L['lang_sel']}**")
        lang_choice = st.radio("Lang", ["Tiếng Việt", "English"],
                               index=0 if st.session_state.lang == 'vi' else 1,
                               label_visibility="collapsed")
        st.divider()
        if st.button(L['about']):
            st.toast(L['team_info'])
            
        new_theme = theme_choice.lower()
        new_lang = 'vi' if lang_choice == "Tiếng Việt" else 'en'
        
        if new_theme != st.session_state.theme or new_lang != st.session_state.lang:
            st.session_state.theme = new_theme
            st.session_state.lang = new_lang
            st.rerun()

# Nội dung
st.title(L['title'])
st.caption(L['sub'])
st.markdown("---")

col_left, col_right = st.columns([1.3, 1], gap="large")

with col_left:
    with st.container(border=True):
        st.markdown(L['input_header'])
        u_input = st.text_area(L['input_label'], placeholder=L['input_placeholder'], height=130)
        
        if st.button(L['btn_send']):
            progress_text = L['loading']
            my_bar = st.progress(0, text=progress_text)
            for percent_complete in range(100):
                time.sleep(0.01)
                my_bar.progress(percent_complete + 1, text=progress_text)
            time.sleep(0.5)
            my_bar.empty()
            st.success("✅ Đã tìm thấy các địa điểm phù hợp nhất!")

    # Map
    map_data = pd.DataFrame({
        'lat': [10.776, 10.802, 10.785], 
        'lon': [106.701, 106.695, 106.690], 
        'name': ['A', 'B', 'C']
    })
    
    m_style = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json" if st.session_state.theme == 'dark' else "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
    
    st.pydeck_chart(pdk.Deck(
        layers=[
            pdk.Layer(
                "ScatterplotLayer", 
                map_data, 
                get_position='[lon, lat]', 
                get_color='[255, 75, 75, 200]', 
                get_radius=120, 
                pickable=True
            ),
            pdk.Layer(
                "ScatterplotLayer", 
                map_data, 
                get_position='[lon, lat]', 
                get_color='[255, 75, 75, 50]', 
                get_radius=300, 
                pickable=False
            )
        ],
        initial_view_state=pdk.ViewState(
            latitude=10.788, 
            longitude=106.695, 
            zoom=12.5, 
            pitch=45 
        ),
        map_style=m_style
    ))

with col_right:
    st.subheader(L['suggest_title'])
    for i in range(3):
        with st.container(border=True):
            c1, c2 = st.columns([1, 1.5])
            with c1: 
                st.image(f"https://picsum.photos/400/300?random={i+99}")
            with c2:
                st.markdown(f"**Location {i+1}**")
                st.caption(f"💰 {L['price']}: 200k")
                st.button(L['detail'], key=f"det_{i}")