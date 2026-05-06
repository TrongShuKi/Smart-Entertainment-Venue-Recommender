import streamlit as st
# Import file api_client mà bạn đã cung cấp (giả sử bạn lưu tên file là api_client.py)
import api_client 

st.set_page_config(page_title="Smart Tourism", page_icon="🌍", layout="centered")

st.title("🌍 Smart Tourism System")
st.markdown("Hệ thống gợi ý địa điểm thông minh ứng dụng AI (Guest Mode)")
st.divider()

# Khu vực nhập liệu
user_input = st.text_input(
    "Bạn đang cảm thấy thế nào? Muốn đi đâu?", 
    placeholder="Ví dụ: Đang stress, trời mưa, đi với bồ có 500k trong Thủ Đức..."
)

# Giả lập Tọa độ GPS (Sau này nhóm Frontend sẽ làm chức năng lấy GPS thật)
col1, col2 = st.columns(2)
with col1:
    lat = st.number_input("Vĩ độ (Latitude)", value=10.762622, format="%.6f")
with col2:
    lon = st.number_input("Kinh độ (Longitude)", value=106.660172, format="%.6f")

# Nút gửi yêu cầu
if st.button("🚀 Gợi ý cho tôi", use_container_width=True):
    if user_input.strip() == "":
        st.warning("Vui lòng nhập tâm tư của bạn trước khi tìm kiếm!")
    else:
        with st.spinner("Đang gửi dữ liệu xuống Backend xử lý..."):
            # Gọi hàm từ api_client. Truyền id_token = None để test ở chế độ Khách (Guest)
            response = api_client.get_suggestions(id_token=None, query=user_input, lat=lat, lon=lon)
            
            if response:
                st.success(f"✅ {response.get('message')}")
                
                # Hiển thị Top 3 địa điểm trả về
                st.subheader("🗺️ Top địa điểm dành cho bạn:")
                places = response.get("top_places", [])
                
                for place in places:
                    with st.container(border=True):
                        st.markdown(f"### 📍 {place['name']}")
                        st.markdown(f"**🏷️ Tag:** `{place['tag']}` | **📏 Khoảng cách:** {place['distance']} km")
                        st.markdown(f"**📝 Mô tả:** {place['description']}")
                        st.markdown(f"**💡 Fact thú vị:** *{place['fact']}*")
            else:
                st.error("❌ Lỗi kết nối đến Backend hoặc Server đang tắt!")