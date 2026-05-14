"""
app.py — Giao diện chính Streamlit
====================================
Kết nối đầy đủ với backend FastAPI qua api_client.py
Render bản đồ bằng map.py (Folium)
"""

import streamlit as st
import time
import requests as _req

# ── Import nội bộ ──────────────────────────────────────────────────────────
from api_client import login, signup, get_suggestions, get_history, google_login
from components.map import render_map

# ══════════════════════════════════════════════════════════════════════════════
# CẤU HÌNH TRANG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Smart Entertainment",
    layout="wide",
    page_icon="🌟",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# KHỞI TẠO SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
_DEFAULTS = {
    "lang":        "vi",
    "theme":       "light",
    "id_token":    None,       # Firebase ID token
    "email":       None,
    "uid":         None,
    "suggestions": None,       # SuggestionResponse dict từ backend
    "user_coords": (10.7769, 106.7009),  # Mặc định: trung tâm TP.HCM
    "last_query":  "",
    "history":     [],
    "auth_error":  "",
    "auth_mode":   "login",    # "login" | "signup"
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

#----- Google login hứng token ---------------
query_params = st.query_params

if "id_token" in query_params and not st.session_state.id_token:
    token = query_params["id_token"]
    try:
        user_data = google_login(token)
        
        # Lưu vào trạng thái ứng dụng
        st.session_state.id_token = user_data["idToken"]
        st.session_state.email = user_data["email"]
        st.session_state.uid = user_data["uid"]
        
        # Làm sạch URL và tải lại trang
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Lỗi xác thực Google: {e}")
#-----------------------------

# ══════════════════════════════════════════════════════════════════════════════
# NỘI DUNG ĐA NGÔN NGỮ
# ══════════════════════════════════════════════════════════════════════════════
TEXT = {
    "vi": {
        "title":           "🌟 SMART ENTERTAINMENT",
        "sub":             "Gợi ý điểm vui chơi thông minh tại TP.HCM",
        "input_header":    "#### 💬 Hôm nay bạn muốn trải nghiệm điều gì?",
        "input_label":     "Chia sẻ tâm tư của bạn...",
        "input_ph":        "Ví dụ: Muốn đi chill với bồ, tầm 200k, không muốn chỗ ồn ào...",
        "btn_send":        "🚀 Gợi ý cho tôi",
        "loading":         "🤖 AI đang phân tích và tìm kiếm...",
        "suggest_title":   "🎯 Gợi Ý Dành Riêng Cho Bạn",
        "price":           "Giá vé",
        "rating":          "Đánh giá",
        "distance":        "Khoảng cách",
        "fact":            "💡 Fact thú vị",
        "weather_title":   "🌤️ Thời tiết khu vực",
        "weather_temp":    "Nhiệt độ",
        "weather_rain":    "Xác suất mưa",
        "free":            "Miễn phí",
        "settings":        "Cài đặt",
        "theme_sel":       "Giao diện",
        "lang_sel":        "Ngôn ngữ",
        "about":           "Nhóm T04",
        "no_result":       "Không tìm thấy địa điểm phù hợp. Hãy thử mô tả khác nhé!",
        "error_api":       "❌ Không kết nối được backend. Kiểm tra server đang chạy chưa?",
        "sidebar_title":   "👤 Tài khoản",
        "login_tab":       "Đăng nhập",
        "signup_tab":      "Đăng ký",
        "email_lbl":       "Email",
        "pass_lbl":        "Mật khẩu",
        "btn_login":       "Đăng nhập",
        "btn_signup":      "Đăng ký",
        "btn_logout":      "🚪 Đăng xuất",
        "logged_as":       "Đang đăng nhập:",
        "guest_mode":      "🙂 Chế độ khách (không cần đăng nhập)",
        "history_title":   "📜 Lịch sử tìm kiếm",
        "history_empty":   "Chưa có lịch sử.",
        "history_load":    "Xem lịch sử",
        "context_label":   "📌 Ngữ cảnh AI hiểu được",
        "location_label":  "📍 Vị trí của bạn (tuỳ chọn)",
        "use_default":     "Dùng vị trí mặc định (Trung tâm TP.HCM)",
        "manual_coords":   "Nhập tọa độ thủ công",
        "lat_label":       "Vĩ độ (Latitude)",
        "lon_label":       "Kinh độ (Longitude)",
    },
    "en": {
        "title":           "🌟 SMART ENTERTAINMENT",
        "sub":             "Intelligent venue recommendations in Ho Chi Minh City",
        "input_header":    "#### 💬 What experience are you looking for today?",
        "input_label":     "Share your thoughts...",
        "input_ph":        "E.g. Chill spot for a date, budget 200k, not too crowded...",
        "btn_send":        "🚀 Find my spot",
        "loading":         "🤖 AI is analyzing your request...",
        "suggest_title":   "🎯 Perfect Matches For You",
        "price":           "Price",
        "rating":          "Rating",
        "distance":        "Distance",
        "fact":            "💡 Fun fact",
        "weather_title":   "🌤️ Local Weather",
        "weather_temp":    "Temperature",
        "weather_rain":    "Rain probability",
        "free":            "Free",
        "settings":        "Settings",
        "theme_sel":       "Theme",
        "lang_sel":        "Language",
        "about":           "Team T04",
        "no_result":       "No matching venues found. Try a different description!",
        "error_api":       "❌ Cannot connect to backend. Is the server running?",
        "sidebar_title":   "👤 Account",
        "login_tab":       "Login",
        "signup_tab":      "Sign Up",
        "email_lbl":       "Email",
        "pass_lbl":        "Password",
        "btn_login":       "Login",
        "btn_signup":      "Sign Up",
        "btn_logout":      "🚪 Logout",
        "logged_as":       "Logged in as:",
        "guest_mode":      "🙂 Guest mode (no login required)",
        "history_title":   "📜 Search History",
        "history_empty":   "No history yet.",
        "history_load":    "View history",
        "context_label":   "📌 AI understood context",
        "location_label":  "📍 Your location (optional)",
        "use_default":     "Use default location (HCMC Center)",
        "manual_coords":   "Enter coordinates manually",
        "lat_label":       "Latitude",
        "lon_label":       "Longitude",
    },
}

L = TEXT[st.session_state.lang]

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
WEATHER_ICON = {
    "RAIN": "🌧️", "STORM": "⛈️", "DRIZZLE": "🌦️",
    "CLEAR": "☀️", "CLOUDS": "☁️", "MIST": "🌫️", "SNOW": "❄️",
}

def _price_display(price: int) -> str:
    if price == 0:
        return L["free"]
    return f"{price:,}đ"

def _star_display(rating: float) -> str:
    full = int(rating)
    return "⭐" * full + f" {rating:.1f}"

def _map_places(top_places: list) -> list:
    """Chuyển Place dict từ API → format mà render_map() trong map.py mong đợi."""
    return [
        {
            "coords":        (p["latitude"], p["longitude"]),
            "name":          p["name"],
            "category":      p.get("category", ""),
            "ai_description": p.get("description", ""),
        }
        for p in top_places
        if p.get("latitude") and p.get("longitude")
    ]

def _do_logout():
    for key in ("id_token", "email", "uid", "suggestions", "history", "auth_error"):
        st.session_state[key] = _DEFAULTS[key]
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
def _inject_css(theme: str):
    bg   = "#0e1117" if theme == "dark" else "#f8f9fa"
    fg   = "#ffffff"  if theme == "dark" else "#1a1a2e"
    card = "#1c1f26"  if theme == "dark" else "#ffffff"
    border_col = "#2e3340" if theme == "dark" else "#e0e0e0"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Space Grotesk', sans-serif;
    }}
    .stApp {{
        background-color: {bg};
        color: {fg};
    }}
    [data-testid="stHeader"] {{ background-color: {bg}; }}
    [data-testid="stSidebar"] {{ background-color: {"#161922" if theme=="dark" else "#eef0f5"}; }}

    /* Buttons */
    .stButton > button {{
        width: 100%;
        border-radius: 10px;
        border: 1.5px solid #ff4b4b;
        color: #ff4b4b;
        background: transparent;
        font-weight: 600;
        transition: all 0.25s ease;
        padding: 0.5rem 1rem;
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, #ff4b4b, #ff8080);
        color: #fff;
        border-color: transparent;
    }}

    /* Place cards */
    .place-card {{
        background: {card};
        border: 1px solid {border_col};
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 12px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .place-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 75, 75, 0.15);
    }}
    .place-name {{
        font-size: 1.05rem;
        font-weight: 700;
        color: {"#fff" if theme=="dark" else "#1a1a2e"};
        margin: 0 0 4px 0;
    }}
    .place-tag {{
        display: inline-block;
        background: rgba(255, 75, 75, 0.15);
        color: #ff6b6b;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 6px;
    }}
    .place-meta {{
        font-size: 0.82rem;
        color: {"#aab" if theme=="dark" else "#666"};
        margin: 2px 0;
    }}
    .place-desc {{
        font-size: 0.87rem;
        color: {"#ccc" if theme=="dark" else "#444"};
        margin: 8px 0 6px;
        line-height: 1.5;
        border-left: 3px solid #ff4b4b;
        padding-left: 10px;
    }}
    .place-fact {{
        font-size: 0.8rem;
        color: {"#888" if theme=="dark" else "#888"};
        font-style: italic;
        margin-top: 6px;
    }}

    /* Weather badge */
    .weather-box {{
        background: {card};
        border: 1px solid {border_col};
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 16px;
        display: flex;
        gap: 18px;
        align-items: center;
        flex-wrap: wrap;
    }}
    .weather-item {{
        font-size: 0.88rem;
        color: {"#ccd" if theme=="dark" else "#555"};
    }}
    .weather-item b {{
        color: {"#fff" if theme=="dark" else "#222"};
    }}

    /* Context summary badge */
    .context-badge {{
        background: rgba(255, 75, 75, 0.1);
        border: 1px solid rgba(255, 75, 75, 0.3);
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 0.82rem;
        color: #ff8080;
        margin-bottom: 14px;
        font-weight: 600;
    }}

    /* Rank badge */
    .rank-badge {{
        font-size: 1.4rem;
        font-weight: 800;
        color: #ff4b4b;
    }}
    </style>
    """, unsafe_allow_html=True)

_inject_css(st.session_state.theme)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — XÁC THỰC & LỊCH SỬ
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"### {L['sidebar_title']}")
    st.markdown("---")

    # Đã đăng nhập
    if st.session_state.id_token:
        st.success(f"{L['logged_as']}\n\n**{st.session_state.email}**")

        if st.button(L["btn_logout"], width="stretch"):
            _do_logout()

        st.markdown("---")
        st.markdown(f"**{L['history_title']}**")

        if st.button(L["history_load"], width="stretch"):
            try:
                hist_resp = get_history(st.session_state.id_token, limit=5)
                st.session_state.history = hist_resp.get("history", [])
            except Exception:
                st.session_state.history = []

        if st.session_state.history:
            for item in st.session_state.history:
                ts = item.get("timestamp", "")[:10]
                q  = item.get("query", "—")
                with st.expander(f"📅 {ts} — {q[:30]}…" if len(q) > 30 else f"📅 {ts} — {q}"):
                    for r in item.get("results", []):
                        st.markdown(f"• **{r.get('name', '')}** ({r.get('score', 0):.1f}★)")
        else:
            st.caption(L["history_empty"])

    # Chưa đăng nhập
    else:
        st.caption(L["guest_mode"])
        st.markdown("")

        tab_login, tab_signup = st.tabs([L["login_tab"], L["signup_tab"]])

        with tab_login:
            em_l = st.text_input(L["email_lbl"], key="login_email", placeholder="email@example.com")
            pw_l = st.text_input(L["pass_lbl"],  key="login_pass",  type="password")
            if st.button(L["btn_login"], key="btn_do_login", width="stretch"):
                if em_l and pw_l:
                    try:
                        res = login(em_l, pw_l)
                        st.session_state.id_token = res["idToken"]
                        st.session_state.email    = res["email"]
                        st.session_state.uid      = res["uid"]
                        st.session_state.auth_error = ""
                        st.rerun()
                    except _req.HTTPError as e:
                        st.session_state.auth_error = "Sai email hoặc mật khẩu." if e.response.status_code == 401 else str(e)
                    except Exception as e:
                        st.session_state.auth_error = f"Lỗi kết nối: {e}"
                else:
                    st.session_state.auth_error = "Vui lòng nhập email và mật khẩu."
            if st.session_state.auth_error:
                st.error(st.session_state.auth_error)
            #------Login with Google-----------
            st.markdown("<div style='text-align: center; margin: 15px 0;'><b>HOẶC</b></div>", unsafe_allow_html=True)
            
            google_auth_url = "http://localhost:8000/auth/google/start"
            st.markdown(f"""
                <a href="{google_auth_url}" target="_self" style="text-decoration: none;">
                    <div style="display: flex; align-items: center; justify-content: center; 
                                padding: 8px; border: 1px solid #ddd; border-radius: 8px; 
                                background-color: white; color: #444; font-weight: bold; cursor: pointer;">
                        <img src="https://www.gstatic.com/images/branding/product/1x/gsa_512dp.png" width="18" style="margin-right: 10px;">
                        Đăng nhập với Google
                    </div>
                </a>
            """, unsafe_allow_html=True)
            #-----------------------------------

        with tab_signup:
            em_s = st.text_input(L["email_lbl"], key="signup_email", placeholder="email@example.com")
            pw_s = st.text_input(L["pass_lbl"],  key="signup_pass",  type="password")
            if st.button(L["btn_signup"], key="btn_do_signup", width="stretch"):
                if em_s and pw_s:
                    try:
                        signup(em_s, pw_s)
                        st.success("Tạo tài khoản thành công! Hãy đăng nhập.")
                    except _req.HTTPError as e:
                        detail = e.response.json() if e.response else str(e)
                        st.error(f"Lỗi đăng ký: {detail}")
                    except Exception as e:
                        st.error(f"Lỗi kết nối: {e}")
                else:
                    st.warning("Vui lòng nhập đầy đủ thông tin.")

# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
hdr_col, cfg_col = st.columns([5, 1])

with hdr_col:
    st.title(L["title"])
    st.caption(L["sub"])

with cfg_col:
    with st.popover(f"⚙️ {L['settings']}"):
        st.write(f"**{L['theme_sel']}**")
        theme_pick = st.radio("Theme", ["Dark", "Light"],
                              index=0 if st.session_state.theme == "dark" else 1,
                              label_visibility="collapsed")
        st.divider()
        st.write(f"**{L['lang_sel']}**")
        lang_pick = st.radio("Lang", ["Tiếng Việt", "English"],
                             index=0 if st.session_state.lang == "vi" else 1,
                             label_visibility="collapsed")
        st.divider()
        st.caption("Nhóm T04 · Smart Entertainment")

        new_theme = theme_pick.lower()
        new_lang  = "vi" if lang_pick == "Tiếng Việt" else "en"
        if new_theme != st.session_state.theme or new_lang != st.session_state.lang:
            st.session_state.theme = new_theme
            st.session_state.lang  = new_lang
            st.rerun()

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT CHÍNH: 2 CỘT
# ══════════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1.35, 1], gap="large")

# ── CỘT TRÁI: Input + Bản đồ ──────────────────────────────────────────────
with col_left:

    # Tuỳ chọn vị trí
    with st.expander(L["location_label"], expanded=False):
        loc_mode = st.radio(
            "Chọn chế độ vị trí",
            [L["use_default"], L["manual_coords"]],
            label_visibility="collapsed",
        )
        if loc_mode == L["manual_coords"]:
            c_lat, c_lon = st.columns(2)
            with c_lat:
                user_lat = st.number_input(L["lat_label"], value=10.7769, format="%.4f", step=0.0001)
            with c_lon:
                user_lon = st.number_input(L["lon_label"], value=106.7009, format="%.4f", step=0.0001)
            st.session_state.user_coords = (user_lat, user_lon)
        else:
            st.session_state.user_coords = (10.7769, 106.7009)
        st.caption(f"📍 {st.session_state.user_coords[0]:.4f}, {st.session_state.user_coords[1]:.4f}")

    # Input box + nút gửi
    with st.container(border=True):
        st.markdown(L["input_header"])
        u_input = st.text_area(
            L["input_label"],
            placeholder=L["input_ph"],
            height=115,
            label_visibility="collapsed",
        )

        if st.button(L["btn_send"], width="stretch"):
            if not u_input.strip():
                st.warning("Hãy nhập nội dung trước khi gửi nhé!")
            else:
                # Progress bar
                bar = st.progress(0, text=L["loading"])
                for i in range(1, 91):
                    time.sleep(0.008)
                    bar.progress(i, text=L["loading"])

                lat, lon = st.session_state.user_coords
                token    = st.session_state.id_token  # None nếu guest

                try:
                    result = get_suggestions(token, u_input.strip(), lat, lon)
                    st.session_state.suggestions = result
                    st.session_state.last_query  = u_input.strip()

                    bar.progress(100, text="✅ Hoàn tất!")
                    time.sleep(0.4)
                    bar.empty()
                    st.rerun()

                except _req.HTTPError as e:
                    bar.empty()
                    code = e.response.status_code if e.response else "?"
                    st.error(f"Lỗi {code} từ server: {e.response.text[:200] if e.response else e}")
                except Exception as e:
                    bar.empty()
                    st.error(L["error_api"])
                    st.caption(str(e))

    # ── Bản đồ ──────────────────────────────────────────────────────────────
    suggestions = st.session_state.suggestions
    user_coords = st.session_state.user_coords

    if suggestions and suggestions.get("top_places"):
        places_for_map = _map_places(suggestions["top_places"])
        if places_for_map:
            render_map(user_coords, places_for_map)
        else:
            st.info("Không có tọa độ địa điểm để hiển thị bản đồ.")
    else:
        render_map(user_coords, [])

# ── CỘT PHẢI: Kết quả gợi ý ───────────────────────────────────────────────
with col_right:
    st.subheader(L["suggest_title"])

    suggestions = st.session_state.suggestions

    if not suggestions:
        st.markdown("""
        <div style="text-align:center; padding: 3rem 1rem; opacity: 0.45;">
            <div style="font-size: 3rem;">🗺️</div>
            <p style="margin-top: 1rem; font-size: 0.9rem;">
                Nhập tâm tư của bạn bên trái<br>để AI gợi ý điểm đến phù hợp!
            </p>
        </div>
        """, unsafe_allow_html=True)

    else:
        top_places = suggestions.get("top_places", [])
        weather    = suggestions.get("weather_info")
        ctx_sum    = suggestions.get("user_context_summary", "")

        # Context summary
        if ctx_sum:
            st.markdown(
                f'<div class="context-badge">📌 {ctx_sum}</div>',
                unsafe_allow_html=True,
            )

        # Weather info
        if weather and weather.get("condition"):
            icon  = WEATHER_ICON.get(weather["condition"], "🌡️")
            cond  = weather.get("condition_vi") or weather.get("condition", "")
            temp  = weather.get("temperature", 0)
            rain  = weather.get("rain_probability", 0)
            source_map = {
                "api_name": "API OpenWeatherMap",
                "api_gps":  "API OpenWeatherMap",
                "nlp":      "Người dùng cung cấp",
                "fallback": "Hệ thống"
            }
            src_text = source_map.get(weather.get("source", "fallback"), "Không rõ")
            loc_name = weather.get("location_name", "Không xác định")

            st.markdown(f"""
            <div class="weather-box">
                <span style="font-size:1.8rem">{icon}</span>
                <div class="weather-item"><b>{cond}</b></div>
                <div class="weather-item">🌡️ <b>{temp:.0f}°C</b></div>
                <div class="weather-item">💧 {L['weather_rain']}: <b>{int(rain*100)}%</b></div>
                <div class="weather-item" style="opacity:0.5;font-size:0.75rem">📍 <b>Khu vực:</b> {loc_name}</div>
                <div class="weather-item" style="opacity:0.5;font-size:0.75rem">📡 <b>Nguồn:</b> {src_text}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Thẻ địa điểm
        if not top_places:
            st.warning(L["no_result"])
        else:
            RANK_MEDALS = ["🥇", "🥈", "🥉"]
            for idx, place in enumerate(top_places):
                medal     = RANK_MEDALS[idx] if idx < 3 else f"#{idx+1}"
                tag       = place.get("tag") or place.get("category", "")
                price_str = _price_display(place.get("price", 0))
                rating    = place.get("rating", 0)
                dist      = place.get("distance", 0)
                desc      = place.get("description", "")
                fact      = place.get("fact", "")
                img_url   = place.get("image_url", "")

                with st.container(border=True):
                    # Ảnh + thông tin
                    img_col, info_col = st.columns([1, 1.6])

                    with img_col:
                        if img_url and img_url.startswith("http"):
                            st.image(img_url, width="stretch")
                        else:
                            # Fallback picsum
                            st.image(
                                f"https://picsum.photos/seed/{place.get('id','x')}/400/300",
                                width="stretch",
                            )

                    with info_col:
                        st.markdown(
                            f'<div class="place-name">{medal} {place.get("name", "")}</div>'
                            f'<span class="place-tag">{tag}</span>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<p class="place-meta">💰 {L["price"]}: <b>{price_str}</b></p>'
                            f'<p class="place-meta">{_star_display(rating)}</p>'
                            f'<p class="place-meta">📍 {dist:.1f} km</p>',
                            unsafe_allow_html=True,
                        )

                    # Mô tả AI (full width bên dưới)
                    if desc:
                        st.markdown(
                            f'<div class="place-desc">{desc}</div>',
                            unsafe_allow_html=True,
                        )
                    if fact:
                        st.markdown(
                            f'<div class="place-fact">💡 {fact}</div>',
                            unsafe_allow_html=True,
                        )