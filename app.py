import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import datetime
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
    /* Premium style system */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background-color: #f8fafc;
        color: #1e293b;
    }
    
    /* Top Banner Gradient */
    .top-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #3b82f6 100%);
        padding: 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.2);
    }
    
    .top-banner h1 {
        color: white !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 800 !important;
        font-size: 2.3rem !important;
        margin: 0 !important;
        letter-spacing: -0.03em;
    }
    
    .top-banner p {
        color: #dbeafe !important;
        margin: 8px 0 0 0 !important;
        font-size: 1.1rem;
        font-weight: 500;
    }
    
    /* Premium Metric Card */
    .metric-card {
        padding: 1.25rem;
        border-radius: 12px;
        background: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
        border: 1px solid #f1f5f9;
        border-left: 5px solid #cbd5e1;
        transition: all 0.25s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.05);
    }
    .metric-red { border-left-color: #ef4444; background: linear-gradient(180deg, #ffffff 0%, #fef2f2 100%); }
    .metric-orange { border-left-color: #f97316; background: linear-gradient(180deg, #ffffff 0%, #fff7ed 100%); }
    .metric-yellow { border-left-color: #eab308; background: linear-gradient(180deg, #ffffff 0%, #fefce8 100%); }
    .metric-green { border-left-color: #22c55e; background: linear-gradient(180deg, #ffffff 0%, #f0fdf4 100%); }
    
    /* Warnings Card Layout */
    .warning-item {
        background: white; 
        padding: 1.25rem; 
        border-radius: 10px; 
        margin-bottom: 1rem; 
        border: 1px solid #f1f5f9;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }
    .warning-item:hover {
        border-color: #cbd5e1;
    }
    
    .badge {
        padding: 5px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        display: inline-block;
        letter-spacing: 0.05em;
    }
    .badge-red { background-color: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }
    .badge-orange { background-color: #ffedd5; color: #9a3412; border: 1px solid #fed7aa; }
    .badge-yellow { background-color: #fef9c3; color: #854d0e; border: 1px solid #fef08a; }
    .badge-green { background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    
    /* Styled Forms */
    .stForm {
        background-color: white !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02) !important;
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

# --- TOP BANNER (RENDER ON EVERY PAGE) ---
st.markdown("""
<div class="top-banner">
    <h1>HỆ THỐNG KIỂM SOÁT KHÉP KÍN VÒNG ĐỜI GÓI THẦU (v1)</h1>
    <p>Dự án KĐT Ven sông Vinh | Tự động hóa tính toán & Tư vấn giải pháp AI</p>
</div>
""", unsafe_allow_html=True)

# --- 1. DASHBOARD VIEW ---
if choice == "📊 Dashboard Điều hành":
    st.write("## 📊 Dashboard Tổng quan Hệ thống")
    
    projects = business_logic.get_all_projects_calculated()
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
            <div style="font-size: 0.8rem; color: #64748b; font-weight: 700; letter-spacing: 0.05em;">TỔNG HẠNG MỤC THEO DÕI</div>
            <div style="font-size: 2.3rem; font-weight: 800; color: #0f172a; margin-top: 5px;">{len(active_projects)}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card metric-red">
            <div style="font-size: 0.8rem; color: #b91c1c; font-weight: 700; letter-spacing: 0.05em;">🔴 CẢNH BÁO ĐỎ</div>
            <div style="font-size: 2.3rem; font-weight: 800; color: #991b1b; margin-top: 5px;">{count_red}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
        <div class="metric-card metric-orange">
            <div style="font-size: 0.8rem; color: #c2410c; font-weight: 700; letter-spacing: 0.05em;">🟠 CẢNH BÁO CAM</div>
            <div style="font-size: 2.3rem; font-weight: 800; color: #9a3412; margin-top: 5px;">{count_orange}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="metric-card metric-yellow">
            <div style="font-size: 0.8rem; color: #a16207; font-weight: 700; letter-spacing: 0.05em;">🟡 CẢNH BÁO VÀNG</div>
            <div style="font-size: 2.3rem; font-weight: 800; color: #854d0e; margin-top: 5px;">{count_yellow}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col5:
        st.markdown(f"""
        <div class="metric-card metric-green">
            <div style="font-size: 0.8rem; color: #15803d; font-weight: 700; letter-spacing: 0.05em;">🟢 BÌNH THƯỜNG</div>
            <div style="font-size: 2.3rem; font-weight: 800; color: #166534; margin-top: 5px;">{count_green}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    
    # Financial metrics totals
    total_budget = sum(p['Ngan_sach'] for p in projects if p['Ngan_sach'])
    total_contract = sum(p['Gia_tri_HDCU'] for p in projects if p['Gia_tri_HDCU'])
    total_cost_calc = sum(p['Total_Cost'] for p in active_projects)
    
    st.write("### 💰 Phân tích Ngân sách & Chi phí Hệ thống")
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        st.metric("Tổng Ngân sách Kế hoạch", f"{total_budget:,.2f} tỷ VNĐ")
    with fcol2:
        st.metric("Tổng Hợp đồng Cung ứng", f"{total_contract:,.2f} tỷ VNĐ")
    with fcol3:
        st.metric("Tổng Chi phí Thực tế Lũy kế", f"{total_cost_calc:,.2f} tỷ VNĐ", delta=f"{total_cost_calc - total_contract:,.2f} tỷ phát sinh")

    st.divider()
    
    # Action Header
    ecol1, ecol2 = st.columns([8, 2])
    with ecol1:
        st.write("### 📌 Danh sách các hạng mục cảnh báo cần xử lý (RED/ORANGE)")
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
        st.success("🎉 Hệ thống hoạt động tốt! Không có rủi ro Đỏ hoặc Cam nào được phát hiện.")
    else:
        for p in critical_projects:
            color_badge = "badge-red" if p['Co_Canh_bao'] == 'RED' else "badge-orange"
            text_color = "🔴 ĐỎ" if p['Co_Canh_bao'] == 'RED' else "🟠 CAM"
            
            st.markdown(f"""
            <div class="warning-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.1rem; font-weight: 700; color: #1e3a8a;">{p['Hang_muc']} (Mã BSC: {p['Ma_BSC']})</span>
                    <span class="badge {color_badge}">{text_color}</span>
                </div>
                <div style="margin-top: 8px; font-size: 0.9rem; color: #475569;">
                    <strong>Phụ trách:</strong> {p['Phu_trach']} | 
                    <strong>Nhóm:</strong> {p['Nhom_CT']} | 
                    <strong>Ngân sách:</strong> {p['Ngan_sach'] or 0.0:.2f} tỷ | 
                    <strong>Tổng chi thực tế:</strong> {p['Total_Cost'] or 0.0:.2f} tỷ
                </div>
                <div style="margin-top: 8px; color: #dc2626; font-weight: 600; font-size: 0.9rem; background-color: #fff5f5; padding: 8px 12px; border-radius: 6px; border: 1px solid #fee2e2;">
                    ⚠️ Chi tiết: {p['Canh_bao_Text']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Gemini AI Solutions
            with st.expander(f"🤖 Đề xuất Phương án & Biện pháp Đẩy nhanh Tiến độ (Gemini AI) cho {p['Ma_BSC']}"):
                if st.button("💡 Tạo giải pháp xử lý rủi ro xây dựng", key=f"risk_btn_{p['id']}"):
                    with st.spinner("Gemini AI đang tổng hợp giải pháp kỹ thuật xây dựng nâng cao..."):
                        try:
                            solutions = ai_service.get_risk_advisor_solutions(p, st.session_state.get('gemini_api_key'))
                            st.markdown(solutions)
                        except Exception as ex:
                            st.error(f"Lỗi: {ex}")

# --- 2. MASTER TABLE VIEW ---
elif choice == "📋 Bảng Tổng hợp (Master)":
    st.write("## 📋 Bảng Tổng hợp Master (BANG TONG HOP)")
    
    projects = business_logic.get_all_projects_calculated()
    
    # Filter/Group by Nhóm CT
    nhom_ct_list = sorted(list(set([p['Nhom_CT'] for p in projects if p['Nhom_CT']])))
    
    # Add new item
    with st.expander("➕ Thêm mới Hạng mục công việc (WBS)"):
        with st.form("add_project_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_tt = st.text_input("Mã TT (Ví dụ: 3, 2.1, 2.2.1)")
                new_ma_bsc = st.text_input("Mã BSC (Nếu là hạng mục WBS cấp con, hãy để trống)")
                new_goi_thau = st.text_input("Gói thầu (PL)")
            with c2:
                new_nhom_ct = st.selectbox("Nhóm công trình", ["Hạ tầng kỹ thuật", "Xây dựng dân dụng", "Công trình phục vụ KD"])
                new_hang_muc = st.text_input("Tên Hạng mục / Công việc *")
                new_phu_trach = st.text_input("Kỹ sư Phụ trách")
            with c3:
                new_ngan_sach = st.number_input("Ngân sách phê duyệt (tỷ)", min_value=0.0, step=0.1)
                new_ngay_bd = st.date_input("Ngày bắt đầu (Yêu cầu CĐT)", value=None)
                new_ngay_kt = st.date_input("Ngày kết thúc (Yêu cầu CĐT)", value=None)
                
            submitted = st.form_submit_button("Lưu Hạng mục")
            if submitted:
                if not new_hang_muc:
                    st.error("Vui lòng nhập Tên Hạng mục / Công việc.")
                else:
                    conn = database.get_connection()
                    cursor = conn.cursor()
                    
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

    # Dynamic Tabs for grouped views - MATCHING THE RED HIGHLIGHT IN IMAGES AND UX SMOOTHNESS
    st.write("### 📑 Bộ lọc các cột theo chức năng kiểm soát")
    tab_labels = [
        "🔴 A. Đầu vào CĐT (Phần khoanh đỏ)",
        "🚚 B. Cung ứng & Hợp đồng",
        "⚡ D. Chốt chặn Khởi công",
        "💰 E. Ngân sách & Chi phí",
        "📊 G. Quản lý Thi công",
        "🏢 Tất cả dữ liệu"
    ]
    t1, t2, t3, t4, t5, t6 = st.tabs(tab_labels)
    
    def render_project_grid(proj_list, cols_to_show, key_suffix=""):
        display_list = []
        for p in proj_list:
            is_wbs = not p['Ma_BSC']
            row_dict = {}
            for col_key, col_name in cols_to_show.items():
                if col_key == "Ma_BSC" and not p['Ma_BSC']:
                    row_dict[col_name] = "--- WBS ---"
                elif col_key in ("DK1_HSKT", "DK2_HDCU", "DK3_KHTK"):
                    row_dict[col_name] = "N/A" if is_wbs else ("✔" if p[col_key] else "✘")
                elif col_key in ("Dieu_kien_du", "Co_Canh_bao"):
                    row_dict[col_name] = "---" if is_wbs else p[col_key]
                elif col_key in ("KH_Thang", "KQ_Thang") and p[col_key] is not None:
                    row_dict[col_name] = f"{p[col_key] * 100:.1f}%"
                else:
                    row_dict[col_name] = p[col_key] if p[col_key] is not None else ""
            display_list.append(row_dict)
            
        df = pd.DataFrame(display_list)
        st.dataframe(df, hide_index=True, use_container_width=True, key=f"grid_{key_suffix}")

    # Tabs rendering logic
    for g_name in nhom_ct_list:
        st.write(f"---")
        st.write(f"### 🏢 Nhóm công trình: **{g_name}**")
        group_projects = [p for p in projects if p['Nhom_CT'] == g_name]
        
        # 1. TAB A: ĐẦU VÀO CĐT (Missing columns from image red box)
        with t1:
            cols_a = {
                "TT": "TT",
                "Ma_BSC": "Mã BSC",
                "Hang_muc": "Hạng mục / Công việc",
                "Phu_trach": "Phụ trách",
                "Ngay_BD_YC": "Ngày BD (YC CĐT)",
                "Ngay_KT_YC": "Ngày KT (YC CĐT)",
                "Ngan_sach": "Ngân sách (tỷ)",
                "KH_phat_hanh_HSTKTC": "KH phát hành HSTKTC",
                "TT_HSTKTC": "TT HSTKTC",
                "TT_SPECS": "TT SPECS",
                "TT_BOQ": "TT BOQ/KL"
            }
            render_project_grid(group_projects, cols_a, f"a_{g_name}")
            
        # 2. TAB B: CUNG ỨNG
        with t2:
            cols_b = {
                "TT": "TT",
                "Ma_BSC": "Mã BSC",
                "Hang_muc": "Hạng mục / Công việc",
                "KH_LCNT": "KH LCNT",
                "TT_LCNT": "TT LCNT",
                "KH_Ky_HDCU": "KH Ký HĐCU",
                "TT_Ky_HDCU": "TT Ký HĐCU",
                "Gia_tri_HDCU": "Giá trị HĐCU (tỷ)",
                "Percent_HDCU_NS": "% HĐ/NS (Tính)"
            }
            render_project_grid(group_projects, cols_b, f"b_{g_name}")

        # 3. TAB D: CHỐT CHẶN KHỞI CÔNG
        with t3:
            cols_c = {
                "TT": "TT",
                "Ma_BSC": "Mã BSC",
                "Hang_muc": "Hạng mục / Công việc",
                "DK1_HSKT": "ĐK1 HSKT đủ",
                "DK2_HDCU": "ĐK2 HĐCU ký",
                "DK3_KHTK": "ĐK3 KHTK duyệt",
                "Dieu_kien_du": "ĐIỀU KIỆN ĐỦ",
                "Ngay_BD_Khoi_Cong": "NGÀY KHỞI CÔNG",
                "Approved_HSo_Count": "HS tiền KC (duyệt)"
            }
            render_project_grid(group_projects, cols_c, f"c_{g_name}")

        # 4. TAB E: NGÂN SÁCH
        with t4:
            cols_d = {
                "TT": "TT",
                "Ma_BSC": "Mã BSC",
                "Hang_muc": "Hạng mục / Công việc",
                "Ngan_sach": "Ngân sách (tỷ)",
                "Luy_ke_HDCU": "Lũy kế HĐ A-B",
                "Luy_ke_Phat_sinh": "Lũy kế Phát sinh B-B'",
                "Total_Cost": "Tổng Chi phí Thực tế",
                "Co_Canh_bao": "Trạng thái Cảnh báo"
            }
            render_project_grid(group_projects, cols_d, f"d_{g_name}")

        # 5. TAB G: QUẢN LÝ THI CÔNG
        with t5:
            cols_g = {
                "TT": "TT",
                "Ma_BSC": "Mã BSC",
                "Hang_muc": "Hạng mục / Công việc",
                "KH_Thang": "KH KLCV Tháng",
                "KQ_Thang": "KQ KLCV Thực tế",
                "Danh_gia_Thang": "Đánh giá & Giải pháp Tháng",
                "T1_KQ": "T1 KQ",
                "T2_KQ": "T2 KQ",
                "T3_KQ": "T3 KQ",
                "T4_KQ": "T4 KQ"
            }
            render_project_grid(group_projects, cols_g, f"g_{g_name}")

        # 6. TAB ALL
        with t6:
            cols_all = {
                "TT": "TT",
                "Ma_BSC": "Mã BSC",
                "Goi_thau": "Gói thầu (PL)",
                "Hang_muc": "Hạng mục / Công việc",
                "Phu_trach": "Phụ trách",
                "Ngay_BD_YC": "Ngày BD",
                "Ngay_KT_YC": "Ngày KT",
                "Ngan_sach": "Ngân sách",
                "Dieu_kien_du": "Khởi công",
                "Co_Canh_bao": "Cảnh báo"
            }
            render_project_grid(group_projects, cols_all, f"all_{g_name}")

        # Action layout
        st.write("⚙️ *Hành động nhanh cho Nhóm:*")
        cols = st.columns(4)
        with cols[0]:
            p_to_edit = st.selectbox("Chọn hạng mục chỉnh sửa tiến trình", [f"{p['id']} - {p['Hang_muc']}" for p in group_projects], key=f"sel_edit_{g_name}")
        
        with cols[1]:
            if st.button("✏️ Cập nhật tiến trình", key=f"btn_edit_{g_name}"):
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

    # Form updating details (Redesigned to be tabs based and super smooth)
    if st.session_state.get('show_edit_form') and st.session_state.get('edit_project_id'):
        p_id = st.session_state['edit_project_id']
        proj = business_logic.get_project_by_id(p_id)
        
        st.divider()
        st.markdown(f"### ✏️ Biểu mẫu Cập nhật chi tiết: **{proj['Hang_muc']}**")
        
        with st.form("edit_project_detail_form"):
            # Sub-tabs inside the edit form for cleanliness
            etab1, etab2, etab3 = st.tabs(["📋 Định danh & Đầu vào CĐT", "🚚 Cung ứng & Hợp đồng", "🚀 Tiến độ Thi công"])
            
            with etab1:
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    e_tt = st.text_input("Mã TT", value=proj['TT'] or "")
                    e_ma_bsc = st.text_input("Mã BSC", value=proj['Ma_BSC'] or "")
                    e_goi_thau = st.text_input("Gói thầu", value=proj['Goi_thau'] or "")
                    e_phu_trach = st.text_input("Người phụ trách", value=proj['Phu_trach'] or "")
                with col_e2:
                    e_ngay_bd = st.date_input("Ngày BĐ (YC CĐT)", value=datetime.datetime.strptime(proj['Ngay_BD_YC'], '%Y-%m-%d').date() if proj['Ngay_BD_YC'] else None)
                    e_ngay_kt = st.date_input("Ngày KT (YC CĐT)", value=datetime.datetime.strptime(proj['Ngay_KT_YC'], '%Y-%m-%d').date() if proj['Ngay_KT_YC'] else None)
                    e_ngan_sach = st.number_input("Ngân sách (tỷ)", min_value=0.0, value=proj['Ngan_sach'] or 0.0, step=0.1)
                    
            with etab2:
                col_e3, col_e4 = st.columns(2)
                with col_e3:
                    st.write("**Hồ sơ Thiết kế & Khảo sát:**")
                    e_kh_hstk = st.date_input("KH phát hành HSTKTC", value=datetime.datetime.strptime(proj['KH_phat_hanh_HSTKTC'], '%Y-%m-%d').date() if proj['KH_phat_hanh_HSTKTC'] else None)
                    e_tt_hstk = st.selectbox("TT HSTKTC", ["Chưa có TK", "Đang TK", "Điều chỉnh TK", "Đã phát hành", "Hoàn thiện"], index=["Chưa có TK", "Đang TK", "Điều chỉnh TK", "Đã phát hành", "Hoàn thiện"].index(proj['TT_HSTKTC'] or "Chưa có TK"))
                    e_tt_specs = st.selectbox("TT SPECS", ["Chưa có", "Đang lập", "Đã cấp"], index=["Chưa có", "Đang lập", "Đã cấp"].index(proj['TT_SPECS'] or "Chưa có"))
                    e_tt_boq = st.selectbox("TT BOQ/KL", ["Chưa bàn giao", "Đang lập", "Điều chỉnh", "Đã bàn giao"], index=["Chưa bàn giao", "Đang lập", "Điều chỉnh", "Đã bàn giao"].index(proj['TT_BOQ'] or "Chưa bàn giao"))
                with col_e4:
                    st.write("**Hợp đồng Cung ứng:**")
                    e_kh_lcnt = st.date_input("KH LCNT", value=datetime.datetime.strptime(proj['KH_LCNT'], '%Y-%m-%d').date() if proj['KH_LCNT'] else None)
                    e_tt_lcnt = st.selectbox("TT LCNT", ["Chưa LCNT", "Đang mời thầu", "Đang đánh giá", "Đã có KQ", "Đã ký"], index=["Chưa LCNT", "Đang mời thầu", "Đang đánh giá", "Đã có KQ", "Đã ký"].index(proj['TT_LCNT'] or "Chưa LCNT"))
                    e_kh_hdcu = st.date_input("KH Ký HĐCU", value=datetime.datetime.strptime(proj['KH_Ky_HDCU'], '%Y-%m-%d').date() if proj['KH_Ky_HDCU'] else None)
                    e_tt_hdcu = st.selectbox("TT Ký HĐCU", ["Chưa CU", "Đang trình ký", "Đã CU", "Theo đợt TC"], index=["Chưa CU", "Đang trình ký", "Đã CU", "Theo đợt TC"].index(proj['TT_Ky_HDCU'] or "Chưa CU"))
                    e_val_hdcu = st.number_input("Giá trị HĐ Cung ứng (tỷ)", min_value=0.0, value=proj['Gia_tri_HDCU'] or 0.0, step=0.1)

            with etab3:
                col_e5, col_e6 = st.columns(2)
                with col_e5:
                    st.write("**Thời gian & Kế hoạch:**")
                    e_ngay_kc = st.date_input("Ngày Khởi công", value=datetime.datetime.strptime(proj['Ngay_BD_Khoi_Cong'], '%Y-%m-%d').date() if proj['Ngay_BD_Khoi_Cong'] else None)
                    e_tt_khtk = st.selectbox("TT KHTK", ["Chưa trình", "Đang duyệt", "Đã duyệt"], index=["Chưa trình", "Đang duyệt", "Đã duyệt"].index(proj['TT_KHTK'] or "Chưa trình"))
                    e_kh_thang = st.number_input("Kế hoạch sản lượng tháng (%)", min_value=0.0, max_value=100.0, value=float((proj['KH_Thang'] or 0.0) * 100)) / 100.0
                    e_kq_thang = st.number_input("Kết quả sản lượng thực tế (%)", min_value=0.0, max_value=100.0, value=float((proj['KQ_Thang'] or 0.0) * 100)) / 100.0
                with col_e6:
                    st.write("**Phân tích Tiến độ:**")
                    e_danh_gia = st.text_area("Đánh giá tiến độ & giải pháp hành động", value=proj['Danh_gia_Thang'] or "")

            submitted_edit = st.form_submit_button("Lưu thay đổi")
            if submitted_edit:
                conn = database.get_connection()
                cursor = conn.cursor()
                
                bd_str = e_ngay_bd.strftime('%Y-%m-%d') if e_ngay_bd else None
                kt_str = e_ngay_kt.strftime('%Y-%m-%d') if e_ngay_kt else None
                kh_hstk_str = e_kh_hstk.strftime('%Y-%m-%d') if e_kh_hstk else None
                kh_lcnt_str = e_kh_lcnt.strftime('%Y-%m-%d') if e_kh_lcnt else None
                kh_hdcu_str = e_kh_hdcu.strftime('%Y-%m-%d') if e_kh_hdcu else None
                kc_str = e_ngay_kc.strftime('%Y-%m-%d') if e_ngay_kc else None
                
                cursor.execute("""
                    UPDATE master_bang_tonghop
                    SET TT = ?, Ma_BSC = ?, Goi_thau = ?, Phu_trach = ?, Ngay_BD_YC = ?, Ngay_KT_YC = ?, Ngan_sach = ?,
                        KH_phat_hanh_HSTKTC = ?, TT_HSTKTC = ?, TT_SPECS = ?, TT_BOQ = ?,
                        KH_LCNT = ?, TT_LCNT = ?, KH_Ky_HDCU = ?, TT_Ky_HDCU = ?, Gia_tri_HDCU = ?,
                        Ngay_BD_Khoi_Cong = ?, TT_KHTK = ?, KH_Thang = ?, KQ_Thang = ?, Danh_gia_Thang = ?
                    WHERE id = ?
                """, (
                    e_tt, e_ma_bsc, e_goi_thau, e_phu_trach, bd_str, kt_str, e_ngan_sach,
                    kh_hstk_str, e_tt_hstk, e_tt_specs, e_tt_boq,
                    kh_lcnt_str, e_tt_lcnt, kh_hdcu_str, e_tt_hdcu, e_val_hdcu,
                    kc_str, e_tt_khtk, e_kh_thang, e_kq_thang, e_danh_gia, p_id
                ))
                
                conn.commit()
                conn.close()
                st.success("Đã lưu các thay đổi cho hạng mục thành công!")
                st.session_state['show_edit_form'] = False
                st.rerun()

# --- 3. SUB-TABLE 01: HỒ SƠ TIỀN KHỞI CÔNG ---
elif choice == "📂 01. Hồ sơ Tiền khởi công":
    st.write("## 📂 Sổ 01 - Hồ sơ Tiền khởi công")
    st.write("Quản lý danh sách các hồ sơ đầu vào bắt buộc duyệt trước khi Khởi công.")
    
    bsc_options = load_ma_bsc_options()
    
    with st.expander("➕ Thêm mới Hồ sơ"):
        with st.form("add_hso_form"):
            c1, c2 = st.columns(2)
            with c1:
                sel_bsc = st.selectbox("Dự án liên kết (Mã BSC)", [f"{opt['Ma_BSC']} - {opt['Hang_muc']}" for opt in bsc_options])
                h_loai = st.selectbox("Loại hồ sơ", ['HSTKTC', 'SPECS', 'BOQ/KL', 'KQ LCNT', 'HĐCU', 'PD KHCU', 'Ký PLHĐ', 'PD KHTK'])
                h_ten = st.text_input("Tên tài liệu / Số hiệu văn bản *")
                h_link = st.text_input("Đường dẫn lưu trữ (LINK)")
            with c2:
                h_ngay = st.date_input("Ngày ký / hoàn thành", value=datetime.date.today())
                h_nguoi_lap = st.text_input("Kỹ sư lập")
                h_nguoi_duyet = st.text_input("Kỹ sư duyệt")
                h_tt = st.selectbox("Trạng thái duyệt", ['Chưa lập', 'Đang lập', 'Chờ duyệt', 'Đã duyệt', 'Từ chối'], index=3)
                
            submitted_hso = st.form_submit_button("Lưu Hồ sơ")
            if submitted_hso:
                if not h_ten:
                    st.error("Vui lòng nhập Tên hồ sơ.")
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
                    st.success("Thêm mới hồ sơ thành công!")
                    st.rerun()

    conn = database.get_connection()
    df_hso = pd.read_sql_query("SELECT id, Ma_BSC, Hang_muc, Loai_ho_so, Ten_san_pham, Link_luu_tru, Ngay_HT, Nguoi_lap, Nguoi_duyet, TT_duyet FROM hso_tienkc", conn)
    conn.close()
    st.dataframe(df_hso, hide_index=True, use_container_width=True)

# --- 4. SUB-TABLE 02: KẾ HOẠCH THÁNG/TUẦN ---
elif choice == "📅 02. Kế hoạch Tháng/Tuần":
    st.write("## 📅 Sổ 02 - Kế hoạch Triển khai Tháng/Tuần")
    st.write("Kiểm soát việc trình duyệt 5 tài liệu bắt buộc theo tuần/tháng.")
    
    bsc_options = load_ma_bsc_options()
    
    with st.expander("➕ Trình duyệt Kế hoạch Mới"):
        with st.form("add_kh_form"):
            c1, c2 = st.columns(2)
            with c1:
                sel_bsc = st.selectbox("Chọn dự án (Mã BSC)", [f"{opt['Ma_BSC']} - {opt['Hang_muc']}" for opt in bsc_options])
                kh_thang = st.text_input("Tháng kiểm soát (Ví dụ: 06/2026)", value="06/2026")
                kh_loai = st.selectbox("Loại tài liệu kế hoạch", ['Biện pháp thi công', 'Kế hoạch cung ứng', 'Biểu đồ nhân lực', 'Biểu đồ máy móc thiết bị', 'Biểu đồ cung ứng'])
                kh_nd = st.text_input("Nội dung đệ trình chính *")
                kh_yckt = st.selectbox("Đạt yêu cầu kỹ thuật CĐT?", ['Có', 'Chưa', 'Đang sửa đổi'], index=0)
            with c2:
                kh_link = st.text_input("LINK tài liệu đính kèm")
                kh_tt_lap = st.selectbox("Trạng thái lập", ['Chưa lập', 'Đang lập', 'Đã lập'], index=2)
                kh_tt_duyet = st.selectbox("Trạng thái duyệt", ['Chưa lập', 'Đang lập', 'Chờ duyệt', 'Đã duyệt', 'Từ chối'], index=3)
                kh_nguoi_lap = st.text_input("Nhà thầu lập")
                kh_nguoi_duyet = st.text_input("Cán bộ duyệt")
                kh_ngay_duyet = st.date_input("Ngày phê duyệt", value=datetime.date.today())
                
            submitted_kh = st.form_submit_button("Lưu Kế hoạch")
            if submitted_kh:
                if not kh_nd:
                    st.error("Vui lòng điền Nội dung đệ trình chính.")
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
                    st.success("Trình kế hoạch thành công!")
                    st.rerun()

    conn = database.get_connection()
    df_kh = pd.read_sql_query("SELECT * FROM kh_thang_tuan", conn)
    conn.close()
    st.dataframe(df_kh, hide_index=True, use_container_width=True)

# --- 5. SUB-TABLE 03: QUẢN LÝ PHÁT SINH ---
elif choice == "⚠️ 03. Quản lý Phát sinh":
    st.title("⚠️ Sổ 03 - Phát sinh & Sai khác")
    
    bsc_options = load_ma_bsc_options()
    
    with st.expander("➕ Báo cáo Phát sinh"):
        with st.form("add_ps_form"):
            c1, c2 = st.columns(2)
            with c1:
                ps_ma = st.text_input("Mã Phát sinh (Ví dụ: PS.CT01.03) *")
                sel_bsc = st.selectbox("Mã BSC ảnh hưởng", [f"{opt['Ma_BSC']} - {opt['Hang_muc']}" for opt in bsc_options])
                ps_ngay = st.date_input("Ngày lập phiếu", value=datetime.date.today())
                ps_loai = st.selectbox("Phân loại phát sinh", ['Phát sinh khối lượng', 'Sai khác thiết kế', 'Biện pháp thi công phát sinh', 'Khác'])
                ps_mota = st.text_area("Chi tiết mô tả")
                ps_nguyennhan = st.text_area("Nguyên nhân cốt lõi")
            with c2:
                ps_dexuat = st.text_area("Đề xuất hướng xử lý")
                ps_giatri = st.number_input("Giá trị dự toán phát sinh (tỷ)", min_value=0.0, step=0.1)
                ps_tg = st.number_input("Thời gian chậm tiến độ dự kiến (ngày)", min_value=0, step=1)
                ps_link = st.text_input("LINK văn bản phát sinh")
                ps_tt = st.selectbox("Trạng thái duyệt", ['Chờ duyệt', 'Đã duyệt', 'Nháp'])
                ps_nguoi_duyet = st.text_input("Cán bộ thẩm định/duyệt")
                
            submitted_ps = st.form_submit_button("Lưu Đệ trình")
            if submitted_ps:
                if not ps_ma:
                    st.error("Vui lòng nhập Mã phát sinh.")
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
                    st.success("Đệ trình thành công!")
                    st.rerun()

    conn = database.get_connection()
    df_ps = pd.read_sql_query("SELECT * FROM phat_sinh", conn)
    conn.close()
    st.dataframe(df_ps, hide_index=True, use_container_width=True)

# --- 6. SUB-TABLE 04: CUNG ỨNG ĐẶC THÙ ---
elif choice == "🚚 04. Cung ứng Đặc thù":
    st.title("🚚 Sổ 04 - Cung ứng Vật tư Đặc thù / Đột xuất")
    
    bsc_options = load_ma_bsc_options()
    
    with st.expander("➕ Yêu cầu Mua sắm Đặc thù"):
        with st.form("add_cu_form"):
            c1, c2 = st.columns(2)
            with c1:
                cu_ma = st.text_input("Mã yêu cầu (Ví dụ: YC.CT01.03) *")
                sel_bsc = st.selectbox("Mã BSC gói thầu", [f"{opt['Ma_BSC']} - {opt['Hang_muc']}" for opt in bsc_options])
                cu_ngay = st.date_input("Ngày đệ trình mua sắm", value=datetime.date.today())
                cu_loai = st.selectbox("Tính chất đệ trình", ['Đặc thù', 'Đột xuất', 'Thay thế vật liệu'])
                cu_vt = st.text_input("Tên vật tư / Thiết bị *")
                cu_lydo = st.text_area("Đặc tả yêu cầu & Lý do thay đổi")
            with c2:
                cu_kl = st.number_input("Khối lượng yêu cầu", min_value=0.0, step=1.0)
                cu_dvt = st.text_input("Đơn vị tính (ĐVT)")
                cu_gia = st.number_input("Giá trị dự toán (tỷ)", min_value=0.0, step=0.01)
                cu_trong_ngoai = st.selectbox("Trong/Ngoài phạm vi HĐCU", ['Trong HĐCU', 'Ngoài HĐCU'])
                cu_link = st.text_input("LINK tài liệu kỹ thuật")
                cu_tt = st.selectbox("Trạng thái duyệt đệ trình", ['Chờ duyệt', 'Đã duyệt'])
                cu_nguoi_duyet = st.text_input("Người duyệt")
                
            submitted_cu = st.form_submit_button("Lưu Yêu cầu")
            if submitted_cu:
                if not cu_ma or not cu_vt:
                    st.error("Vui lòng nhập đầy đủ Mã yêu cầu và Tên vật tư.")
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
                    st.success("Đã ghi nhận yêu cầu cung ứng vật tư!")
                    st.rerun()

    conn = database.get_connection()
    df_cu = pd.read_sql_query("SELECT * FROM cu_dac_thu", conn)
    conn.close()
    st.dataframe(df_cu, hide_index=True, use_container_width=True)

# --- 7. SUB-TABLE 05: BÙ TIỀN ĐỘ ---
elif choice == "🚀 05. Bù Tiến độ":
    st.title("🚀 Sổ 05 - Phương án Bù Tiến độ")
    
    bsc_options = load_ma_bsc_options()
    
    with st.expander("➕ Thiết lập Phương án Bù Tiến độ"):
        with st.form("add_bu_form"):
            c1, c2 = st.columns(2)
            with c1:
                sel_bsc = st.selectbox("Chọn dự án bị chậm", [f"{opt['Ma_BSC']} - {opt['Hang_muc']}" for opt in bsc_options])
                bu_ngay = st.date_input("Ngày lập phương án", value=datetime.date.today())
                bu_cham = st.number_input("Số ngày bị trễ (ngày)", min_value=1.0, step=1.0)
                bu_nguyennhan = st.text_area("Nguyên nhân cốt lõi chậm trễ")
                bu_pa = st.text_input("Tên giải pháp bù nhanh *")
            with c2:
                bu_chitiet = st.text_area("Kế hoạch triển khai chi tiết")
                bu_moc = st.date_input("Hạn cuối cam kết bù xong")
                bu_link = st.text_input("LINK phương án được duyệt")
                bu_tt_duyet = st.selectbox("Tình trạng duyệt phương án", ['Chờ duyệt', 'Đã duyệt'])
                bu_nguoi = st.text_input("Cán bộ duyệt")
                bu_kq = st.text_input("Đánh giá kết quả thực hiện bù")
                bu_tt_trienkhai = st.selectbox("Trạng thái triển khai", ['Đang thực hiện', 'Đã hoàn thành', 'Đóng'])
                
            submitted_bu = st.form_submit_button("Lưu Phương án")
            if submitted_bu:
                if not bu_pa:
                    st.error("Vui lòng điền Tên giải pháp bù.")
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
                    st.success("Thiết lập phương án bù tiến độ thành công!")
                    st.rerun()

    conn = database.get_connection()
    df_bu = pd.read_sql_query("SELECT * FROM bu_tien_do", conn)
    conn.close()
    st.dataframe(df_bu, hide_index=True, use_container_width=True)

# --- 8. AI ASSISTANT VIEW ---
elif choice == "🤖 Trợ lý AI Thông minh":
    st.title("🤖 Trợ lý AI Phân tích Báo cáo Xây dựng")
    
    st.info(
        "Nhập báo cáo tiến độ tuần bằng ngôn ngữ tự nhiên từ công trường. Trợ lý AI sẽ: \n"
        "1. Xác định đúng hạng mục công việc và Mã BSC tương ứng.\n"
        "2. Điền kết quả tiến độ và nguyên nhân vào Bảng tổng hợp.\n"
        "3. Tự động khởi tạo phiếu khắc phục bù tiến độ ở trạng thái 'Đang thực hiện' trong Sổ 05."
    )
    
    raw_report = st.text_area(
        "📝 Nhập báo cáo thô của tuần:",
        height=150,
        placeholder="Ví dụ: Báo cáo hạng mục CT-01 Nhà mẫu tuần này đã đạt 22%, chậm 3% do mưa bão lớn kéo dài và nền đất bị sụt yếu. Công trường đang phải bố trí tăng ca đêm để lấy lại tiến độ."
    )
    
    if st.button("🚀 Phân tích & Đồng bộ vào Hệ thống", type="primary"):
        if not raw_report:
            st.warning("Vui lòng nhập báo cáo trước.")
        else:
            with st.spinner("AI đang giải trình và liên kết dữ liệu hệ thống..."):
                try:
                    projects = business_logic.get_all_projects_calculated()
                    parsed_json = ai_service.parse_raw_report(
                        raw_report, 
                        projects, 
                        st.session_state.get('gemini_api_key')
                    )
                    
                    st.success("🤖 Phân tích AI hoàn tất!")
                    st.json(parsed_json)
                    
                    ma_bsc_matched = parsed_json.get("ma_bsc")
                    week_index = parsed_json.get("week_index")
                    week_kq = parsed_json.get("week_kq")
                    week_danh_gia = parsed_json.get("week_danh_gia")
                    bu_info = parsed_json.get("bu_tien_do")
                    
                    if not ma_bsc_matched:
                        st.warning("⚠️ Không tìm thấy Mã BSC phù hợp tương ứng trong báo cáo này.")
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
                            st.write(f"✅ Đã tự động cập nhật kết quả tuần {week_index} vào dòng Master.")
                            
                        # 2. Insert into 05_Bu_tien_do
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
                            st.write("✅ Đã tự động thêm 1 dòng phương án bù tiến độ (Sổ 05) ở trạng thái 'Đang thực hiện'.")
                            
                        conn.commit()
                        conn.close()
                        st.success("🎉 Hệ thống đã được đồng bộ dữ liệu tự động thành công!")
                except Exception as ex:
                    st.error(f"Lỗi: {ex}")
