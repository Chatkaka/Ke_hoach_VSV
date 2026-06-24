import streamlit as st
import pandas as pd
import datetime
import os
import json
import io

# Import local modules
import database
import business_logic
import exporter
import ai_service

# Initialize database on startup
database.init_db()

# --- Page Config ---
st.set_page_config(
    page_title="Hệ thống Kiểm soát Gói thầu Thi công",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling ---
st.markdown("""
<style>
    /* CSS for premium look */
    .stApp {
        background-color: #f7f9fc;
        color: #1e293b;
    }
    h1, h2, h3 {
        font-family: 'Outfit', 'Inter', sans-serif;
        color: #0f172a;
    }
    .metric-card {
        padding: 20px;
        border-radius: 12px;
        background: white;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);
        border-left: 5px solid #cbd5e1;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-red { border-left-color: #ef4444; background-color: #fef2f2; }
    .metric-orange { border-left-color: #f97316; background-color: #fff7ed; }
    .metric-yellow { border-left-color: #eab308; background-color: #fefce8; }
    .metric-green { border-left-color: #22c55e; background-color: #f0fdf4; }
    
    .badge {
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-red { background-color: #fee2e2; color: #991b1b; }
    .badge-orange { background-color: #ffedd5; color: #9a3412; }
    .badge-yellow { background-color: #fef9c3; color: #854d0e; }
    .badge-green { background-color: #dcfce7; color: #166534; }
    
    .wbs-row {
        background-color: #f8fafc;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.markdown("# 🖥️ HỆ THỐNG KIỂM SOÁT")
st.sidebar.markdown("### Closed-Loop Procurement & Construction")
st.sidebar.divider()

# API Key handling
api_key_env = os.environ.get("GEMINI_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "🔑 Google Gemini API Key",
    type="password",
    value=api_key_env,
    help="Nhập API Key của bạn để sử dụng Trợ lý AI và Cố vấn Rủi ro."
)
if api_key_input:
    st.session_state['gemini_api_key'] = api_key_input
else:
    st.session_state['gemini_api_key'] = api_key_env

# Navigation
menu_options = [
    "📊 Dashboard Điều hành",
    "📋 Bảng Tổng hợp (Master)",
    "📂 01. Hồ sơ Tiền khởi công",
    "📅 02. Kế hoạch Tháng/Tuần",
    "⚠️ 03. Quản lý Phát sinh",
    "🚚 04. Cung ứng Đặc thù",
    "🚀 05. Bù Tiến độ",
    "🤖 Trợ lý AI Thông minh"
]
choice = st.sidebar.radio("📌 Phân hệ chức năng", menu_options)

st.sidebar.divider()
st.sidebar.info(
    "💡 **Hệ thống Kiểm soát Khép kín** giúp liên kết kế hoạch, tiến độ, chi phí và "
    "cung ứng đặc thù dựa trên Mã BSC của từng gói thầu."
)

# Helper function to load projects list for dropdowns
def load_ma_bsc_options():
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, Ma_BSC, Hang_muc FROM master_bang_tonghop WHERE Ma_BSC IS NOT NULL AND Ma_BSC != ''")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "Ma_BSC": r[1], "Hang_muc": r[2]} for r in rows]

# --- 1. DASHBOARD VIEW ---
if choice == "📊 Dashboard Điều hành":
    st.title("📊 Dashboard Điều hành Hệ thống")
    st.subheader("Dự án KĐT Ven sông Vinh | Trực quan hóa Rủi ro & Tiến độ")
    
    projects = business_logic.get_all_projects_calculated()
    
    # Calculate summary KPIs (Only count projects that have Ma_BSC)
    active_projects = [p for p in projects if p['Ma_BSC']]
    
    count_red = sum(1 for p in active_projects if p['Co_Canh_bao'] == 'RED')
    count_orange = sum(1 for p in active_projects if p['Co_Canh_bao'] == 'ORANGE')
    count_yellow = sum(1 for p in active_projects if p['Co_Canh_bao'] == 'YELLOW')
    count_green = sum(1 for p in active_projects if p['Co_Canh_bao'] == 'GREEN')
    
    # Render KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; color: #64748b; font-weight: 600;">TỔNG HẠNG MỤC</div>
            <div style="font-size: 2.2rem; font-weight: 700; color: #0f172a; margin-top: 5px;">{len(active_projects)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card metric-red">
            <div style="font-size: 0.9rem; color: #b91c1c; font-weight: 600;">🔴 CẢNH BÁO ĐỎ</div>
            <div style="font-size: 2.2rem; font-weight: 700; color: #991b1b; margin-top: 5px;">{count_red}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card metric-orange">
            <div style="font-size: 0.9rem; color: #c2410c; font-weight: 600;">🟠 CẢNH BÁO CAM</div>
            <div style="font-size: 2.2rem; font-weight: 700; color: #9a3412; margin-top: 5px;">{count_orange}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="metric-card metric-yellow">
            <div style="font-size: 0.9rem; color: #a16207; font-weight: 600;">🟡 CẢNH BÁO VÀNG</div>
            <div style="font-size: 2.2rem; font-weight: 700; color: #854d0e; margin-top: 5px;">{count_yellow}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col5:
        st.markdown(f"""
        <div class="metric-card metric-green">
            <div style="font-size: 0.9rem; color: #15803d; font-weight: 600;">🟢 BÌNH THƯỜNG (XANH)</div>
            <div style="font-size: 2.2rem; font-weight: 700; color: #166534; margin-top: 5px;">{count_green}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    
    # Export and Refresh Section
    ecol1, ecol2 = st.columns([8, 2])
    with ecol1:
        st.write("### 📌 Danh sách Hạng mục cần Hành động (Đỏ & Cam)")
    with ecol2:
        # Excel Export Button
        try:
            excel_stream = exporter.get_excel_report_stream()
            st.download_button(
                label="📥 Xuất báo cáo Excel (.xlsx)",
                data=excel_stream,
                file_name=f"Bao_Cao_Kiem_Soat_Du_An_{datetime.date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_export_excel",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Lỗi xuất Excel: {e}")

    # Show delayed or budget overrun projects
    critical_projects = [p for p in active_projects if p['Co_Canh_bao'] in ('RED', 'ORANGE')]
    
    if not critical_projects:
        st.success("🎉 Tuyệt vời! Hiện tại không có hạng mục nào gặp rủi ro Đỏ hoặc Cam.")
    else:
        for p in critical_projects:
            color_badge = "badge-red" if p['Co_Canh_bao'] == 'RED' else "badge-orange"
            text_color = "🔴 ĐỎ" if p['Co_Canh_bao'] == 'RED' else "🟠 CAM"
            
            with st.container():
                st.markdown(f"""
                <div style="background: white; padding: 20px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; color: #0f172a;">{p['Hang_muc']} (Mã: {p['Ma_BSC']})</h4>
                        <span class="badge {color_badge}">{text_color}</span>
                    </div>
                    <p style="margin: 10px 0 5px 0; font-size: 0.95rem;">
                        <strong>Phụ trách:</strong> {p['Phu_trach']} | 
                        <strong>Nhóm công trình:</strong> {p['Nhom_CT']} | 
                        <strong>Khởi công:</strong> {p['Ngay_BD_Khoi_Cong'] or 'Chưa có'}
                    </p>
                    <p style="margin: 0 0 10px 0; color: #e11d48; font-weight: 600; font-size: 0.95rem;">
                        ⚠️ Lý do cảnh báo: {p['Canh_bao_Text']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Gemini AI Solutions
                with st.expander(f"🤖 Xem giải pháp khắc phục từ Gemini AI cho {p['Ma_BSC']}"):
                    if st.button("🚀 Tạo kế hoạch hành động khắc phục rủi ro", key=f"risk_btn_{p['id']}"):
                        with st.spinner("Đang kết nối Gemini AI để phân tích và đề xuất giải pháp..."):
                            try:
                                solutions = ai_service.get_risk_advisor_solutions(p, st.session_state.get('gemini_api_key'))
                                st.markdown(solutions)
                            except Exception as ex:
                                st.error(f"Lỗi: {ex}")

# --- 2. MASTER TABLE VIEW ---
elif choice == "📋 Bảng Tổng hợp (Master)":
    st.title("📋 Bảng Tổng hợp Tiến độ - Kế hoạch - Cung ứng (Master)")
    
    projects = business_logic.get_all_projects_calculated()
    
    # Filter/Group by Nhóm CT
    nhom_ct_list = sorted(list(set([p['Nhom_CT'] for p in projects if p['Nhom_CT']])))
    
    # Add new item modal/button
    with st.expander("➕ Thêm mới Hạng mục (WBS)"):
        with st.form("add_project_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_tt = st.text_input("TT (Ví dụ: 3, 2.1, 2.2.1)")
                new_ma_bsc = st.text_input("Mã BSC (Bỏ trống đối với WBS thành phần)")
                new_goi_thau = st.text_input("Gói thầu (PL)")
            with c2:
                new_nhom_ct = st.selectbox("Nhóm công trình", ["Hạ tầng kỹ thuật", "Xây dựng dân dụng", "Công trình phục vụ KD"])
                new_hang_muc = st.text_input("Hạng mục / Công việc *")
                new_phu_trach = st.text_input("Phụ trách")
            with c3:
                new_ngan_sach = st.number_input("Ngân sách (tỷ đồng)", min_value=0.0, step=0.1)
                new_ngay_bd = st.date_input("Ngày bắt đầu (Yêu cầu CĐT)", value=None)
                new_ngay_kt = st.date_input("Ngày kết thúc (Yêu cầu CĐT)", value=None)
                
            submitted = st.form_submit_button("Lưu Hạng mục")
            if submitted:
                if not new_hang_muc:
                    st.error("Vui lòng điền tên Hạng mục / Công việc.")
                else:
                    conn = database.get_connection()
                    cursor = conn.cursor()
                    
                    # Convert dates
                    bd_str = new_ngay_bd.strftime('%Y-%m-%d') if new_ngay_bd else None
                    kt_str = new_ngay_kt.strftime('%Y-%m-%d') if new_ngay_kt else None
                    
                    cursor.execute("""
                        INSERT INTO master_bang_tonghop (TT, Ma_BSC, Goi_thau, Nhom_CT, Hang_muc, Phu_trach, Ngay_BD_YC, Ngay_KT_YC, Ngan_sach)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (new_tt, new_ma_bsc, new_goi_thau, new_nhom_ct, new_hang_muc, new_phu_trach, bd_str, kt_str, new_ngan_sach))
                    conn.commit()
                    conn.close()
                    st.success("Đã thêm hạng mục mới thành công!")
                    st.rerun()

    # Display grouped table
    for g_name in nhom_ct_list:
        st.write(f"## 🏢 Nhóm công trình: {g_name}")
        group_projects = [p for p in projects if p['Nhom_CT'] == g_name]
        
        # Prepare tabular dataframe to render
        display_data = []
        for p in group_projects:
            is_wbs = not p['Ma_BSC'] # Sub-item WBS has blank Ma_BSC
            
            # Format row display dictionary
            row_dict = {
                "ID": p['id'],
                "TT": p['TT'],
                "Mã BSC": p['Ma_BSC'] or "--- WBS ---",
                "Hạng mục": p['Hang_muc'],
                "Ngân sách (tỷ)": p['Ngan_sach'] if p['Ngan_sach'] else "",
                "Khởi công kế hoạch": p['Ngay_BD_Khoi_Cong'] or "",
                "ĐK1 HSKT": "N/A" if is_wbs else ("✔" if p['DK1_HSKT'] else "✘"),
                "ĐK2 HĐCU": "N/A" if is_wbs else ("✔" if p['DK2_HDCU'] else "✘"),
                "ĐK3 KHTK": "N/A" if is_wbs else ("✔" if p['DK3_KHTK'] else "✘"),
                "Điều kiện Khởi công": "---" if is_wbs else p['Dieu_kien_du'],
                "Cảnh báo": "---" if is_wbs else p['Co_Canh_bao']
            }
            display_data.append(row_dict)
            
        df_group = pd.DataFrame(display_data)
        
        # Render table with styled colors
        st.dataframe(
            df_group,
            column_config={
                "Cảnh báo": st.column_config.TextColumn(
                    "Cảnh báo",
                    help="Trạng thái cảnh báo hệ thống"
                ),
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Actions for rows (Edit/Delete)
        st.write("🔧 *Hành động nhanh cho Nhóm công trình:*")
        cols = st.columns(4)
        with cols[0]:
            p_to_edit = st.selectbox("Chọn hạng mục để sửa/cập nhật tiến trình", [f"{p['id']} - {p['Hang_muc']}" for p in group_projects], key=f"sel_edit_{g_name}")
        
        with cols[1]:
            if st.button("✏️ Cập nhật thông tin chi tiết", key=f"btn_edit_{g_name}"):
                p_id = int(p_to_edit.split(" - ")[0])
                st.session_state['edit_project_id'] = p_id
                st.session_state['show_edit_form'] = True
                
        with cols[2]:
            if st.button("🗑️ Xóa hạng mục", key=f"btn_delete_{g_name}"):
                p_id = int(p_to_edit.split(" - ")[0])
                conn = database.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM master_bang_tonghop WHERE id = ?", (p_id,))
                conn.commit()
                conn.close()
                st.success("Đã xóa hạng mục thành công!")
                st.rerun()

    # Render Edit Form if active
    if st.session_state.get('show_edit_form') and st.session_state.get('edit_project_id'):
        p_id = st.session_state['edit_project_id']
        proj = business_logic.get_project_by_id(p_id)
        
        st.divider()
        st.markdown(f"### ✏️ Cập nhật Tiến trình Hạng mục: **{proj['Hang_muc']}**")
        
        # Form to edit fields
        with st.form("edit_project_detail_form"):
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.subheader("1. Hồ sơ Thiết kế & Khảo sát")
                e_tt_hstk = st.selectbox("TT HSTKTC", ["Chưa có TK", "Đang TK", "Điều chỉnh TK", "Đã phát hành", "Hoàn thiện"], index=["Chưa có TK", "Đang TK", "Điều chỉnh TK", "Đã phát hành", "Hoàn thiện"].index(proj['TT_HSTKTC'] or "Chưa có TK"))
                e_tt_specs = st.selectbox("TT SPECS", ["Chưa có", "Đang lập", "Đã cấp"], index=["Chưa có", "Đang lập", "Đã cấp"].index(proj['TT_SPECS'] or "Chưa có"))
                e_tt_boq = st.selectbox("TT BOQ/KL", ["Chưa bàn giao", "Đang lập", "Điều chỉnh", "Đã bàn giao"], index=["Chưa bàn giao", "Đang lập", "Điều chỉnh", "Đã bàn giao"].index(proj['TT_BOQ'] or "Chưa bàn giao"))
                e_ngay_kc = st.date_input("Ngày BĐ Khởi công", value=datetime.datetime.strptime(proj['Ngay_BD_Khoi_Cong'], '%Y-%m-%d').date() if proj['Ngay_BD_Khoi_Cong'] else None)

            with c2:
                st.subheader("2. Hợp đồng & Cung ứng")
                e_tt_hdcu = st.selectbox("TT Ký HĐCU", ["Chưa CU", "Đang trình ký", "Đã CU", "Theo đợt TC"], index=["Chưa CU", "Đang trình ký", "Đã CU", "Theo đợt TC"].index(proj['TT_Ky_HDCU'] or "Chưa CU"))
                e_val_hdcu = st.number_input("Giá trị HĐ Cung ứng (tỷ)", min_value=0.0, value=proj['Gia_tri_HDCU'] or 0.0, step=0.1)
                e_tt_khtk = st.selectbox("TT KHTK", ["Chưa trình", "Đang duyệt", "Đã duyệt"], index=["Chưa trình", "Đang duyệt", "Đã duyệt"].index(proj['TT_KHTK'] or "Chưa trình"))
                e_phu_trach = st.text_input("Người phụ trách", value=proj['Phu_trach'] or "")

            with c3:
                st.subheader("3. Kiểm soát Tiến độ Tháng")
                e_kh_thang = st.number_input("Kế hoạch sản lượng tháng (%)", min_value=0.0, max_value=100.0, value=float((proj['KH_Thang'] or 0.0) * 100)) / 100.0
                e_kq_thang = st.number_input("Kết quả sản lượng thực tế (%)", min_value=0.0, max_value=100.0, value=float((proj['KQ_Thang'] or 0.0) * 100)) / 100.0
                e_danh_gia = st.text_area("Đánh giá sản lượng & Giải pháp", value=proj['Danh_gia_Thang'] or "")
                
            submitted_edit = st.form_submit_button("Lưu thay đổi")
            if submitted_edit:
                conn = database.get_connection()
                cursor = conn.cursor()
                
                kc_str = e_ngay_kc.strftime('%Y-%m-%d') if e_ngay_kc else None
                
                cursor.execute("""
                    UPDATE master_bang_tonghop
                    SET TT_HSTKTC = ?, TT_SPECS = ?, TT_BOQ = ?, TT_Ky_HDCU = ?, Gia_tri_HDCU = ?, 
                        TT_KHTK = ?, Ngay_BD_Khoi_Cong = ?, KH_Thang = ?, KQ_Thang = ?, Danh_gia_Thang = ?, Phu_trach = ?
                    WHERE id = ?
                """, (e_tt_hstk, e_tt_specs, e_tt_boq, e_tt_hdcu, e_val_hdcu, e_tt_khtk, kc_str, e_kh_thang, e_kq_thang, e_danh_gia, e_phu_trach, p_id))
                
                conn.commit()
                conn.close()
                st.success("Đã cập nhật tiến trình thành công!")
                st.session_state['show_edit_form'] = False
                st.rerun()

# --- 3. SUB-TABLE 01: HỒ SƠ TIỀN KHỞI CÔNG ---
elif choice == "📂 01. Hồ sơ Tiền khởi công":
    st.title("📂 Sổ 01 - Hồ sơ Tiền khởi công")
    st.write("Quản lý danh sách các sản phẩm/hồ sơ bắt buộc hoàn thành trước khi được phép phát lệnh Khởi công.")
    
    # Load options
    bsc_options = load_ma_bsc_options()
    
    with st.expander("➕ Thêm mới Hồ sơ Tiền khởi công"):
        with st.form("add_hso_form"):
            c1, c2 = st.columns(2)
            with c1:
                sel_bsc = st.selectbox("Mã BSC dự án", [f"{opt['Ma_BSC']} - {opt['Hang_muc']}" for opt in bsc_options])
                h_loai = st.selectbox("Loại hồ sơ", ['HSTKTC', 'SPECS', 'BOQ/KL', 'KQ LCNT', 'HĐCU', 'PD KHCU', 'Ký PLHĐ', 'PD KHTK'])
                h_ten = st.text_input("Tên sản phẩm / Số hiệu *")
                h_link = st.text_input("LINK lưu trữ hồ sơ")
            with c2:
                h_ngay = st.date_input("Ngày hoàn thành", value=datetime.date.today())
                h_nguoi_lap = st.text_input("Người lập")
                h_nguoi_duyet = st.text_input("Người duyệt")
                h_tt = st.selectbox("Trạng thái duyệt", ['Chưa lập', 'Đang lập', 'Chờ duyệt', 'Đã duyệt', 'Từ chối'], index=3) # Default: Đã duyệt
                
            submitted_hso = st.form_submit_button("Lưu Hồ sơ")
            if submitted_hso:
                if not h_ten:
                    st.error("Vui lòng nhập Tên sản phẩm / Số hiệu.")
                else:
                    ma_bsc_val = sel_bsc.split(" - ")[0]
                    hang_muc_val = sel_bsc.split(" - ")[1]
                    ngay_str = h_ngay.strftime('%Y-%m-%d') if h_ngay else None
                    
                    conn = database.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO hso_tienkc (Ma_BSC, Hang_muc, Loai_ho_so, Ten_san_pham, Link_luu_tru, Ngay_HT, Nguoi_lap, Nguoi_duyet, TT_duyet)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (ma_bsc_val, hang_muc_val, h_loai, h_ten, h_link, ngay_str, h_nguoi_lap, h_nguoi_duyet, h_tt))
                    conn.commit()
                    conn.close()
                    st.success("Đã thêm mới hồ sơ tiền khởi công thành công!")
                    st.rerun()

    # Load and display
    conn = database.get_connection()
    df_hso = pd.read_sql_query("SELECT id, Ma_BSC, Hang_muc, Loai_ho_so, Ten_san_pham, Link_luu_tru, Ngay_HT, Nguoi_lap, Nguoi_duyet, TT_duyet FROM hso_tienkc", conn)
    conn.close()
    
    st.dataframe(df_hso, hide_index=True, use_container_width=True)

# --- 4. SUB-TABLE 02: KẾ HOẠCH THÁNG/TUẦN ---
elif choice == "📅 02. Kế hoạch Tháng/Tuần":
    st.title("📅 Sổ 02 - Kế hoạch Triển khai Tháng/Tuần")
    st.write("Bắt buộc trình duyệt 5 tài liệu trước đầu tháng: Biện pháp thi công, Kế hoạch cung ứng, Biểu đồ nhân lực, Biểu đồ máy móc thiết bị, Biểu đồ cung ứng.")
    
    bsc_options = load_ma_bsc_options()
    
    with st.expander("➕ Trình duyệt Tài liệu Kế hoạch"):
        with st.form("add_kh_form"):
            c1, c2 = st.columns(2)
            with c1:
                sel_bsc = st.selectbox("Mã BSC dự án", [f"{opt['Ma_BSC']} - {opt['Hang_muc']}" for opt in bsc_options])
                kh_thang = st.text_input("Tháng (Ví dụ: 06/2026)", value="06/2026")
                kh_loai = st.selectbox("Loại tài liệu", ['Biện pháp thi công', 'Kế hoạch cung ứng', 'Biểu đồ nhân lực', 'Biểu đồ máy móc thiết bị', 'Biểu đồ cung ứng'])
                kh_nd = st.text_input("Nội dung chính *")
                kh_yckt = st.selectbox("Đạt yêu cầu kỹ thuật CĐT?", ['Có', 'Chưa', 'Đang sửa đổi'], index=0)
            with c2:
                kh_link = st.text_input("LINK tài liệu")
                kh_tt_lap = st.selectbox("Trạng thái lập", ['Chưa lập', 'Đang lập', 'Đã lập'], index=2)
                kh_tt_duyet = st.selectbox("Trạng thái duyệt", ['Chưa lập', 'Đang lập', 'Chờ duyệt', 'Đã duyệt', 'Từ chối'], index=3)
                kh_nguoi_lap = st.text_input("Người lập")
                kh_nguoi_duyet = st.text_input("Người duyệt")
                kh_ngay_duyet = st.date_input("Ngày duyệt", value=datetime.date.today())
                
            submitted_kh = st.form_submit_button("Lưu Kế hoạch")
            if submitted_kh:
                if not kh_nd:
                    st.error("Vui lòng điền Nội dung chính.")
                else:
                    ma_bsc_val = sel_bsc.split(" - ")[0]
                    hang_muc_val = sel_bsc.split(" - ")[1]
                    ngay_duyet_str = kh_ngay_duyet.strftime('%Y-%m-%d') if kh_ngay_duyet else None
                    
                    conn = database.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO kh_thang_tuan (Ma_BSC, Hang_muc, Thang, Loai_tai_lieu, Noi_dung_chinh, Dat_YCKT_CDT, Link_tai_lieu, TT_lap, TT_duyet, Nguoi_lap, Nguoi_duyet, Ngay_duyet)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (ma_bsc_val, hang_muc_val, kh_thang, kh_loai, kh_nd, kh_yckt, kh_link, kh_tt_lap, kh_tt_duyet, kh_nguoi_lap, kh_nguoi_duyet, ngay_duyet_str))
                    conn.commit()
                    conn.close()
                    st.success("Đã trình kế hoạch mới thành công!")
                    st.rerun()

    conn = database.get_connection()
    df_kh = pd.read_sql_query("SELECT * FROM kh_thang_tuan", conn)
    conn.close()
    
    st.dataframe(df_kh, hide_index=True, use_container_width=True)

# --- 5. SUB-TABLE 03: QUẢN LÝ PHÁT SINH ---
elif choice == "⚠️ 03. Quản lý Phát sinh":
    st.title("⚠️ Sổ 03 - Phát sinh & Sai khác")
    st.write("Theo dõi, thẩm định và phê duyệt các phát sinh khối lượng hoặc sai khác thiết kế trong thi công.")
    
    bsc_options = load_ma_bsc_options()
    
    with st.expander("➕ Đệ trình Phát sinh mới"):
        with st.form("add_ps_form"):
            c1, c2 = st.columns(2)
            with c1:
                ps_ma = st.text_input("Mã phát sinh (Ví dụ: PS.CT01.03) *")
                sel_bsc = st.selectbox("Mã BSC liên đới", [f"{opt['Ma_BSC']} - {opt['Hang_muc']}" for opt in bsc_options])
                ps_ngay = st.date_input("Ngày phát sinh", value=datetime.date.today())
                ps_loai = st.selectbox("Loại phát sinh", ['Phát sinh khối lượng', 'Sai khác thiết thiết kế', 'Biện pháp thi công phát sinh', 'Khác'])
                ps_mota = st.text_area("Mô tả phát sinh")
                ps_nguyennhan = st.text_area("Nguyên nhân")
            with c2:
                ps_dexuat = st.text_area("Đề xuất xử lý")
                ps_giatri = st.number_input("Giá trị phát sinh dự kiến (tỷ đồng)", min_value=0.0, step=0.1)
                ps_tg = st.number_input("Ảnh hưởng tiến độ (ngày)", min_value=0, step=1)
                ps_link = st.text_input("LINK hồ sơ / RFI")
                ps_tt = st.selectbox("Trạng thái phê duyệt CĐT", ['Chờ duyệt', 'Đã duyệt', 'Nháp'])
                ps_nguoi_duyet = st.text_input("Người duyệt")
                
            submitted_ps = st.form_submit_button("Lưu Đệ trình")
            if submitted_ps:
                if not ps_ma:
                    st.error("Vui lòng điền Mã phát sinh.")
                else:
                    ma_bsc_val = sel_bsc.split(" - ")[0]
                    hang_muc_val = sel_bsc.split(" - ")[1]
                    ngay_str = ps_ngay.strftime('%Y-%m-%d') if ps_ngay else None
                    
                    conn = database.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO phat_sinh (Ma_PS, Ma_BSC, Hang_muc, Ngay_PS, Loai, Mo_ta, Nguyen_nhan, De_xuat_xu_ly, Gia_tri_phat_sinh, Anh_huong_TD, Link_ho_so, TT_Phe_duyet, Nguoi_duyet)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (ps_ma, ma_bsc_val, hang_muc_val, ngay_str, ps_loai, ps_mota, ps_nguyennhan, ps_dexuat, ps_giatri, ps_tg, ps_link, ps_tt, ps_nguoi_duyet))
                    conn.commit()
                    conn.close()
                    st.success("Đã đệ trình phát sinh mới thành công!")
                    st.rerun()

    conn = database.get_connection()
    df_ps = pd.read_sql_query("SELECT * FROM phat_sinh", conn)
    conn.close()
    
    st.dataframe(df_ps, hide_index=True, use_container_width=True)

# --- 6. SUB-TABLE 04: CUNG ỨNG ĐẶC THÙ ---
elif choice == "🚚 04. Cung ứng Đặc thù":
    st.title("🚚 Sổ 04 - Cung ứng Vật tư Đặc thù / Đột xuất")
    st.write("Quản lý hồ sơ trình duyệt cung ứng các vật tư/thiết bị đặc thù hoặc phát sinh đột xuất ngoài hợp đồng.")
    
    bsc_options = load_ma_bsc_options()
    
    with st.expander("➕ Yêu cầu Cung ứng Vật tư Đặc thù"):
        with st.form("add_cu_form"):
            c1, c2 = st.columns(2)
            with c1:
                cu_ma = st.text_input("Mã yêu cầu (Ví dụ: YC.CT01.03) *")
                sel_bsc = st.selectbox("Mã BSC", [f"{opt['Ma_BSC']} - {opt['Hang_muc']}" for opt in bsc_options])
                cu_ngay = st.date_input("Ngày yêu cầu", value=datetime.date.today())
                cu_loai = st.selectbox("Loại yêu cầu", ['Đặc thù', 'Đột xuất', 'Thay thế chủng loại'])
                cu_vt = st.text_input("Vật tư / Thiết bị *")
                cu_lydo = st.text_area("Đặc tả kỹ thuật / Lý do yêu cầu")
            with c2:
                cu_kl = st.number_input("Khối lượng", min_value=0.0, step=1.0)
                cu_dvt = st.text_input("Đơn vị tính")
                cu_gia = st.number_input("Giá trị dự kiến (tỷ đồng)", min_value=0.0, step=0.01)
                cu_trong_ngoai = st.selectbox("Trong/Ngoài HĐ cung ứng", ['Trong HĐCU', 'Ngoài HĐCU'])
                cu_link = st.text_input("LINK hồ sơ kỹ thuật")
                cu_tt = st.selectbox("Trạng thái phê duyệt", ['Chờ duyệt', 'Đã duyệt'])
                cu_nguoi_duyet = st.text_input("Người duyệt")
                
            submitted_cu = st.form_submit_button("Lưu Yêu cầu")
            if submitted_cu:
                if not cu_ma or not cu_vt:
                    st.error("Vui lòng điền đầy đủ Mã yêu cầu và Tên Vật tư / Thiết bị.")
                else:
                    ma_bsc_val = sel_bsc.split(" - ")[0]
                    hang_muc_val = sel_bsc.split(" - ")[1]
                    ngay_str = cu_ngay.strftime('%Y-%m-%d') if cu_ngay else None
                    
                    conn = database.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO cu_dac_thu (Ma_YC, Ma_BSC, Hang_muc, Ngay_YC, Loai_YC, Vat_tu_thiet_bi, Noi_dung_yeu_cau, KL, DVT, Gia_tri_phat_sinh, Trong_Ngoai_HDCU, Link_ho_so, TT_Phe_duyet, Nguoi_duyet)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (cu_ma, ma_bsc_val, hang_muc_val, ngay_str, cu_loai, cu_vt, cu_lydo, cu_kl, cu_dvt, cu_gia, cu_trong_ngoai, cu_link, cu_tt, cu_nguoi_duyet))
                    conn.commit()
                    conn.close()
                    st.success("Đã ghi nhận yêu cầu cung ứng thành công!")
                    st.rerun()

    conn = database.get_connection()
    df_cu = pd.read_sql_query("SELECT * FROM cu_dac_thu", conn)
    conn.close()
    
    st.dataframe(df_cu, hide_index=True, use_container_width=True)

# --- 7. SUB-TABLE 05: BÙ TIẾN ĐỘ ---
elif choice == "🚀 05. Bù Tiến độ":
    st.title("🚀 Sổ 05 - Phương án Bù Tiến độ")
    st.write("Thiết lập và triển khai các biện pháp bù đắp tiến độ (tăng ca, thêm nhân lực, đổi BPTC) khi dự án bị chậm.")
    
    bsc_options = load_ma_bsc_options()
    
    with st.expander("➕ Lập Phương án Bù Tiến độ"):
        with st.form("add_bu_form"):
            c1, c2 = st.columns(2)
            with c1:
                sel_bsc = st.selectbox("Mã BSC bị chậm", [f"{opt['Ma_BSC']} - {opt['Hang_muc']}" for opt in bsc_options])
                bu_ngay = st.date_input("Ngày phát hiện chậm", value=datetime.date.today())
                bu_cham = st.number_input("Mức chậm (ngày)", min_value=1.0, step=1.0)
                bu_nguyennhan = st.text_area("Nguyên nhân chậm tiến độ")
                bu_pa = st.text_input("Giải pháp bù tóm tắt (Ví dụ: Tăng ca tối) *")
            with c2:
                bu_chitiet = st.text_area("Chi tiết giải pháp triển khai")
                bu_moc = st.date_input("Mốc cam kết hoàn thành bù")
                bu_link = st.text_input("LINK tài liệu phương án")
                bu_tt_duyet = st.selectbox("Trạng thái duyệt phương án", ['Chờ duyệt', 'Đã duyệt'])
                bu_nguoi = st.text_input("Người duyệt")
                bu_kq = st.text_input("Kết quả thực hiện bù")
                bu_tt_trienkhai = st.selectbox("Trạng thái Triển khai", ['Đang thực hiện', 'Đã hoàn thành', 'Đóng'])
                
            submitted_bu = st.form_submit_button("Lưu Phương án")
            if submitted_bu:
                if not bu_pa:
                    st.error("Vui lòng điền Giải pháp bù tóm tắt.")
                else:
                    ma_bsc_val = sel_bsc.split(" - ")[0]
                    hang_muc_val = sel_bsc.split(" - ")[1]
                    ngay_str = bu_ngay.strftime('%Y-%m-%d') if bu_ngay else None
                    moc_str = bu_moc.strftime('%Y-%m-%d') if bu_moc else None
                    
                    conn = database.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO bu_tien_do (Ma_BSC, Hang_muc, Ngay_phat_hien, Muc_cham_ngay, Nguyen_nhan, Phuong_an, Chi_tiet_giai_phap, Moc_cam_ket_HT, Link_phuong_an, TT_duyet, Nguoi_duyet, KQ_thuc_hien_bu, TT_Trien_khai)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (ma_bsc_val, hang_muc_val, ngay_str, bu_cham, bu_nguyennhan, bu_pa, bu_chitiet, moc_str, bu_link, bu_tt_duyet, bu_nguoi, bu_kq, bu_tt_trienkhai))
                    conn.commit()
                    conn.close()
                    st.success("Đã lưu phương án bù tiến độ thành công!")
                    st.rerun()

    conn = database.get_connection()
    df_bu = pd.read_sql_query("SELECT * FROM bu_tien_do", conn)
    conn.close()
    
    st.dataframe(df_bu, hide_index=True, use_container_width=True)

# --- 8. AI ASSISTANT VIEW ---
elif choice == "🤖 Trợ lý AI Thông minh":
    st.title("🤖 Trợ lý AI Thông minh (Gemini API)")
    st.subheader("Nhập liệu thô báo cáo & Tự động chiết xuất thông tin")
    
    st.info(
        "Nhập báo cáo thô tiến độ hàng tuần của công trường vào ô dưới đây. "
        "Gemini AI sẽ tự động phân tích để điền các kết quả tuần, ghi chép nguyên nhân, "
        "và đồng thời chèn 1 dòng kế hoạch bù tiến độ vào Sổ 05 nếu công việc bị trễ."
    )
    
    raw_report = st.text_area(
        "📝 Dán báo cáo thô tại đây:",
        height=150,
        placeholder="Ví dụ: Hạng mục CT-01 tuần này đạt kết quả thực tế là 22%, chậm mất 3% so với kế hoạch do mưa lớn kéo dài và nền đất bị yếu, công trường đang phải tăng ca đêm để bù tiến độ"
    )
    
    if st.button("🚀 Phân tích & Cập nhật Hệ thống", type="primary"):
        if not raw_report:
            st.warning("Vui lòng dán báo cáo thô trước.")
        else:
            with st.spinner("Gemini AI đang làm việc..."):
                try:
                    # Load all projects to match
                    projects = business_logic.get_all_projects_calculated()
                    
                    # Call Gemini Parser
                    parsed_json = ai_service.parse_raw_report(
                        raw_report, 
                        projects, 
                        st.session_state.get('gemini_api_key')
                    )
                    
                    st.success("🤖 Đã phân tích thành công!")
                    st.json(parsed_json)
                    
                    ma_bsc_matched = parsed_json.get("ma_bsc")
                    week_index = parsed_json.get("week_index")
                    week_kq = parsed_json.get("week_kq")
                    week_danh_gia = parsed_json.get("week_danh_gia")
                    bu_info = parsed_json.get("bu_tien_do")
                    
                    if not ma_bsc_matched:
                        st.warning("⚠️ Không tìm thấy Mã BSC phù hợp trong danh sách từ nội dung báo cáo.")
                    else:
                        conn = database.get_connection()
                        cursor = conn.cursor()
                        
                        # 1. Update Master Table weekly fields
                        if week_index and week_index in [1, 2, 3, 4]:
                            kq_col = f"T{week_index}_KQ"
                            dg_col = f"T{week_index}_Danh_gia"
                            
                            cursor.execute(f"""
                                UPDATE master_bang_tonghop 
                                SET {kq_col} = ?, {dg_col} = ? 
                                WHERE Ma_BSC = ?
                            """, (week_kq, week_danh_gia, ma_bsc_matched))
                            st.write(f"✅ Đã cập nhật kết quả tuần {week_index} vào Bảng tổng hợp.")
                            
                        # 2. Insert into 05_Bu_tien_do if needed
                        if bu_info:
                            cursor.execute("SELECT Hang_muc FROM master_bang_tonghop WHERE Ma_BSC = ?", (ma_bsc_matched,))
                            res_h = cursor.fetchone()
                            h_muc_name = res_h[0] if res_h else "Hạng mục thi công"
                            
                            today_str = datetime.date.today().strftime('%Y-%m-%d')
                            
                            cursor.execute("""
                                INSERT INTO bu_tien_do (Ma_BSC, Hang_muc, Ngay_phat_hien, Muc_cham_ngay, Nguyen_nhan, Phuong_an, TT_Trien_khai)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                ma_bsc_matched, 
                                h_muc_name, 
                                today_str, 
                                bu_info.get("muc_cham_ngay", 5.0), 
                                bu_info.get("nguyen_nhan"), 
                                bu_info.get("giai_phap"), 
                                "Đang thực hiện"
                            ))
                            st.write("✅ Đã chèn 1 dòng phương án bù tiến độ mới ở trạng thái 'Đang thực hiện' vào Sổ 05.")
                            
                        conn.commit()
                        conn.close()
                        st.success("🎉 Hệ thống đã được cập nhật dữ liệu tự động từ AI!")
                except Exception as ex:
                    st.error(f"Lỗi khi gọi API hoặc cập nhật cơ sở dữ liệu: {ex}")
