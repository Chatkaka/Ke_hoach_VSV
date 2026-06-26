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

# --- Người dùng hiện tại & Phân quyền ---
def load_users():
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, Ma_NV, Ho_Ten, Chuc_Vu, Vai_Tro, Email, Them_HD, Sua, Xoa_HD, Sua_CDT_BD, Cap_Nhat_CDT FROM nhan_su ORDER BY Ho_Ten ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error loading users: {e}")
        return []

users_list = load_users()
default_user_idx = 0
for idx, u in enumerate(users_list):
    if u['Ho_Ten'] == "Hồ Nghĩa Chất":
        default_user_idx = idx
        break

if users_list:
    selected_user = st.sidebar.selectbox(
        "👤 Người dùng hiện tại:",
        options=users_list,
        format_func=lambda x: f"{x['Ho_Ten']} ({x['Chuc_Vu']})",
        index=default_user_idx
    )
    st.session_state['current_user'] = selected_user
    
    # Hiển thị thông tin phân quyền hiện tại trong sidebar
    is_admin = selected_user.get('Chuc_Vu') == 'Admin' or selected_user.get('Vai_Tro') == 'admin2'
    if is_admin:
        st.sidebar.info("🔓 **Quyền hạn:** Toàn quyền (Admin)")
    else:
        perms = []
        if selected_user.get('Them_HD') == 1: perms.append("Thêm")
        if selected_user.get('Sua') == 1: perms.append("Sửa")
        if selected_user.get('Xoa_HD') == 1: perms.append("Xóa")
        perms_str = ", ".join(perms) if perms else "Chỉ xem"
        st.sidebar.info(f"🔒 **Quyền hạn:** {perms_str}")
else:
    st.sidebar.warning("⚠️ Không thể tải danh sách nhân sự.")
    st.session_state['current_user'] = None

def check_permission(permission_type):
    curr_user = st.session_state.get('current_user')
    if not curr_user:
        return False
    if curr_user.get('Chuc_Vu') == 'Admin' or curr_user.get('Vai_Tro') == 'admin2':
        return True
    return curr_user.get(permission_type) == 1

# Navigation
menu_options = [
    "📊 Dashboard Điều hành",
    "📋 Bảng Tổng hợp (Master)",
    "📂 01. Hồ sơ Tiền khởi công",
    "📅 02. Kế hoạch Tháng/Tuần",
    "⚠️ 03. Quản lý Phát sinh",
    "🚚 04. Cung ứng Đặc thù",
    "🚀 05. Bù Tiến độ",
    "🤖 Trợ lý AI Thông minh",
    "👥 Quản lý Nhân sự"
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

# --- Pandas Styling Helper Functions ---
def style_master_rows(df):
    styles = pd.DataFrame('', index=df.index, columns=df.columns)
    has_bsc_col = "Mã BSC" in df.columns
    for idx in df.index:
        is_wbs = False
            
        if is_wbs:
            for col in df.columns:
                styles.loc[idx, col] = 'background-color: #f1f5f9; color: #475569; font-weight: bold; font-style: italic;'
        else:
            for col in df.columns:
                val = df.loc[idx, col]
                val_str = str(val).strip() if val is not None else ""
                
                # 1. Color warning column
                if col == "Cảnh báo":
                    if "🔴" in val_str:
                        styles.loc[idx, col] = 'background-color: #fee2e2; color: #b91c1c; font-weight: bold;'
                    elif "🟠" in val_str:
                        styles.loc[idx, col] = 'background-color: #ffedd5; color: #c2410c; font-weight: bold;'
                    elif "🟡" in val_str:
                        styles.loc[idx, col] = 'background-color: #fefce8; color: #a16207; font-weight: bold;'
                    elif "🟢" in val_str:
                        styles.loc[idx, col] = 'background-color: #f0fdf4; color: #15803d; font-weight: bold;'
                
                # 2. Status columns
                elif col in ("ĐK1 HSKT đủ", "ĐK2 HĐCU ký", "ĐK3 KHTK duyệt", "ĐIỀU KIỆN ĐỦ", 
                             "TT HSTKTC", "TT SPECS", "TT BOQ/KL", "TT LCNT", "TT Ký HĐCU", "Khởi công"):
                    if val_str in ("✔", "Đã phát hành", "Đã cấp", "Đã bàn giao", "Đã ký", "Đã CU", "Đã duyệt", "Hoàn thiện", "ĐỦ ĐIỀU KIỆN"):
                        styles.loc[idx, col] = 'background-color: #f0fdf4; color: #166534; font-weight: 500;'
                    elif val_str in ("✘", "Chưa có TK", "Chưa có", "Chưa bàn giao", "Chưa LCNT", "Chưa CU", "Chưa trình", "CHƯA ĐỦ ĐK"):
                        styles.loc[idx, col] = 'background-color: #fee2e2; color: #991b1b; font-weight: 500;'
                    elif any(word in val_str for word in ("Đang", "Chờ", "Theo đợt", "Điều chỉnh")):
                        styles.loc[idx, col] = 'background-color: #fefce8; color: #854d0e; font-weight: 500;'
                        
                # 3. Numeric cells color formatting (soft styling)
                elif "% HĐ/NS (Tính)" in col:
                    try:
                        num_val = float(val) if val not in ("", None) else 0.0
                        if num_val > 100.0:
                            styles.loc[idx, col] = 'color: #b91c1c; font-weight: 700;'
                        else:
                            styles.loc[idx, col] = 'color: #15803d; font-weight: 500;'
                    except ValueError:
                        pass
    return styles

def style_subtable_rows(df):
    styles = pd.DataFrame('', index=df.index, columns=df.columns)
    for col in df.columns:
        for idx in df.index:
            val = df.loc[idx, col]
            val_str = str(val).strip() if val is not None else ""
            
            # Highlight statuses
            if col in ("TT_duyet", "TT_lap", "Dat_YCKT_CDT", "TT_Phe_duyet", "TT_Trien_khai", "Trong_Ngoai_HDCU", "TT_cung_ung"):
                if val_str in ("Đã duyệt", "Đã lập", "Có", "Trong HĐCU", "Đã hoàn thành", "Đã ký", "Đã CU"):
                    styles.loc[idx, col] = 'background-color: #f0fdf4; color: #166534; font-weight: 500;'
                elif val_str in ("Chưa lập", "Từ chối", "Chưa", "Ngoài HĐCU", "Từ chối duyệt", "Đóng"):
                    styles.loc[idx, col] = 'background-color: #fee2e2; color: #991b1b; font-weight: 500;'
                elif any(word in val_str for word in ("Đang", "Chờ", "Đang sửa đổi", "Đang thực hiện", "Nháp")):
                    styles.loc[idx, col] = 'background-color: #fefce8; color: #854d0e; font-weight: 500;'
                    
            # Highlight values
            elif col in ("Gia_tri_phat_sinh", "Muc_cham_ngay"):
                try:
                    num_val = float(val) if val not in ("", None) else 0.0
                    if num_val > 0:
                        styles.loc[idx, col] = 'color: #b91c1c; font-weight: 600;'
                except ValueError:
                    pass
    return styles


def render_dataframe_html(df, column_config, key_suffix=""):
    # Vietnamese headers lookup dictionary to auto-translate database columns
    vietnamese_headers = {
        "id": "ID",
        "ma_bsc": "Mã BSC",
        "hang_muc": "Hạng mục",
        "loai_ho_so": "Loại hồ sơ",
        "ten_san_pham": "Tên sản phẩm",
        "link_luu_tru": "Link lưu trữ",
        "ngay_ht": "Ngày hoàn thành",
        "nguoi_lap": "Người lập",
        "nguoi_duyet": "Người duyệt",
        "tt_duyet": "Trạng thái duyệt",
        "thang": "Tháng",
        "loai_tai_lieu": "Loại tài liệu",
        "noi_dung_chinh": "Nội dung chính",
        "dat_yckt_cdt": "Đạt YCKT CĐT?",
        "link_tai_lieu": "Link tài liệu",
        "tt_lap": "TT Lập",
        "ngay_duyet": "Ngày duyệt",
        "ma_ps": "Mã phát sinh",
        "ngay_ps": "Ngày phát sinh",
        "loai": "Phân loại",
        "mo_ta": "Mô tả chi tiết",
        "nguyen_nhan": "Nguyên nhân",
        "de_xuat_xu_ly": "Đề xuất xử lý",
        "gia_tri_phat_sinh": "Giá trị PS (tỷ)",
        "anh_huong_td": "Ảnh hưởng TD (ngày)",
        "link_ho_so": "Link hồ sơ",
        "tt_phe_duyet": "TT Phê duyệt",
        "noi_dung_dieu_chinh": "Nội dung điều chỉnh",
        "ghi_chu": "Ghi chú",
        "ma_yc": "Mã yêu cầu",
        "ngay_yc": "Ngày yêu cầu",
        "loai_yc": "Tính chất",
        "vat_tu_thiet_bi": "Vật tư / Thiết bị",
        "noi_dung_yeu_cau": "Mô tả / Lý do",
        "kl": "Khối lượng",
        "dvt": "Đơn vị tính",
        "trong_ngoai_hdcu": "Phạm vi HĐ",
        "ngay_can": "Ngày cần vật tư",
        "tt_cung_ung": "TT Cung ứng",
        "ngay_phat_hien": "Ngày phát hiện chậm",
        "muc_cham_ngay": "Số ngày trễ",
        "phuong_an": "Giải pháp bù",
        "chi_tiet_giai_phap": "Kế hoạch chi tiết",
        "moc_cam_ket_ht": "Hạn chót cam kết",
        "link_phuong_an": "Link phương án",
        "kq_thuc_hien_bu": "Đánh giá kết quả bù",
        "tt_trien_khai": "TT Triển khai"
    }

    html = []

    css = """
    <style>
        .table-wrapper {
            width: 100%;
            max-height: 500px; /* Constrain height to force vertical scrollbar inside container */
            overflow-y: auto; /* Vertically scrollable */
            overflow-x: hidden; /* Avoid horizontal scrolling */
            border-radius: 12px;
            box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.05), 0 2px 6px -2px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
            margin-bottom: 2rem;
            background: white;
        }
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Inter', sans-serif;
            font-size: 0.775rem;
            color: #334155;
            table-layout: fixed;
        }
        .styled-table th {
            background-color: #f8fafc !important; /* Premium light slate grey background */
            color: #475569 !important; /* Soft slate text */
            font-weight: 700;
            text-align: left;
            padding: 8px 10px;
            position: sticky;
            top: 0;
            z-index: 10;
            border-bottom: 2px solid #e2e8f0;
            font-size: 0.725rem;
            text-transform: uppercase;
            letter-spacing: 0.02em;
            word-wrap: break-word;
            white-space: normal;
            line-height: 1.25;
        }
        /* Sticky header border bottom fix when scrolling */
        .styled-table th::after {
            content: '';
            position: absolute;
            left: 0;
            bottom: 0;
            width: 100%;
            border-bottom: 2px solid #e2e8f0;
        }
        .styled-table td {
            padding: 8px 10px;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: middle;
            word-wrap: break-word;
            white-space: normal;
            line-height: 1.35;
            color: #334155;
        }
        .styled-table tr:hover {
            background-color: #f8fafc !important;
        }
        .styled-table tr.wbs-row {
            background-color: #f8fafc !important;
            font-weight: bold;
            color: #475569;
        }
        .styled-table tr.wbs-row td {
            font-style: italic;
        }
        /* Custom badges */
        .status-badge {
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.725rem;
            font-weight: 600;
            display: inline-block;
            text-align: center;
            line-height: 1.2;
        }
        .badge-green { background-color: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
        .badge-red { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
        .badge-yellow { background-color: #fefce8; color: #a16207; border: 1px solid #fef08a; }
        .badge-orange { background-color: #ffedd5; color: #c2410c; border: 1px solid #fed7aa; }

        /* Link button style */
        .btn-link {
            display: inline-flex;
            align-items: center;
            background-color: #f0fdf4;
            color: #166534;
            border: 1px solid #bbf7d0;
            padding: 3px 6px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 0.725rem;
            font-weight: 500;
            transition: all 0.2s;
        }
        .btn-link:hover {
            background-color: #dcfce7;
            color: #14532d;
            border-color: #86efac;
        }
    </style>
    """
    html.append(css)
    html.append('<div class="table-wrapper">')
    html.append('<table class="styled-table">')

    cols_to_render = []
    for col in df.columns:
        col_lower = col.lower()
        # Find if it is hidden in column_config (case-insensitive)
        cfg_key = None
        for k in column_config.keys():
            if k and k.lower() == col_lower:
                cfg_key = k
                break
        if cfg_key and column_config[cfg_key] is None:
            continue
        cols_to_render.append(col)

    total_cols = len(cols_to_render)
    default_pct = int(100 / max(total_cols, 1))

    # Custom widths for sub-table labels to prevent wrapping overflow
    col_pcts = {
        "Mã BSC": "10%",
        "Hạng mục": "18%",
        "Loại hồ sơ": "10%",
        "Tên hồ sơ / văn bản": "22%",
        "Link lưu trữ": "12%",
        "Ngày hoàn thành": "10%",
        "Người lập": "9%",
        "Người duyệt": "9%",
        "Trạng thái duyệt": "10%",
        # Sổ 02
        "Tháng": "7%",
        "Loại tài liệu": "12%",
        "Nội dung chính": "20%",
        "Đạt YCKT CĐT?": "10%",
        "Link tài liệu": "10%",
        "TT Lập": "9%",
        "TT Duyệt": "9%",
        "Ngày duyệt": "10%",
        # Sổ 03
        "Mã PS": "8%",
        "Ngày PS": "8%",
        "Phân loại": "12%",
        "Mô tả chi tiết": "18%",
        "Nguyên nhân": "13%",
        "Đề xuất xử lý": "13%",
        "Giá trị PS (tỷ)": "9%",
        "Ảnh hưởng TD (ngày)": "9%",
        "Link hồ sơ": "10%",
        "TT Phê duyệt": "10%",
        "Nội dung điều chỉnh": "15%",
        "Ghi chú": "10%",
        # Sổ 04
        "Mã YC": "8%",
        "Ngày yêu cầu": "9%",
        "Tính chất": "8%",
        "Vật tư / Thiết bị": "18%",
        "Mô tả / Lý do": "18%",
        "Khối lượng": "8%",
        "ĐVT": "5%",
        "Giá trị (tỷ)": "8%",
        "Phạm vi HĐ": "10%",
        "Link tài liệu kỹ thuật": "10%",
        "TT Cung ứng": "10%",
        "Ngày cần vật tư": "10%",
        # Sổ 05
        "Ngày phát hiện chậm": "11%",
        "Số ngày trễ": "9%",
        "Nguyên nhân chậm trễ": "18%",
        "Giải pháp bù": "18%",
        "Kế hoạch chi tiết": "18%",
        "Hạn chót cam kết": "10%",
        "Link phương án": "10%",
        "Đánh giá kết quả bù": "15%",
        "TT Triển khai": "10%"
    }

    html.append('<colgroup>')
    for col in cols_to_render:
        col_lower = col.lower()
        label = vietnamese_headers.get(col_lower, col)
        
        cfg_key = None
        for k in column_config.keys():
            if k and k.lower() == col_lower:
                cfg_key = k
                break
                
        if cfg_key:
            cfg = column_config[cfg_key]
            if cfg is not None:
                if isinstance(cfg, str):
                    label = cfg
                elif hasattr(cfg, 'label') and cfg.label:
                    label = cfg.label
                elif hasattr(cfg, 'title') and cfg.title and not callable(cfg.title):
                    label = cfg.title

        width_str = f"{default_pct}%"
        if label in col_pcts:
            width_str = col_pcts[label]
        elif cfg_key:
            cfg = column_config[cfg_key]
            if cfg and hasattr(cfg, 'width') and cfg.width:
                width_str = f"{max(int(cfg.width / 12), 4)}%"

        html.append(f'<col style="width: {width_str};">')
    html.append('</colgroup>')

    html.append('<thead><tr>')
    for col in cols_to_render:
        col_lower = col.lower()
        label = vietnamese_headers.get(col_lower, col)
        
        cfg_key = None
        for k in column_config.keys():
            if k and k.lower() == col_lower:
                cfg_key = k
                break
                
        if cfg_key:
            cfg = column_config[cfg_key]
            if cfg is not None:
                if isinstance(cfg, str):
                    label = cfg
                elif hasattr(cfg, 'label') and cfg.label:
                    label = cfg.label
                elif hasattr(cfg, 'title') and cfg.title and not callable(cfg.title):
                    label = cfg.title

        html.append(f'<th>{label}</th>')
    html.append('</tr></thead>')

    html.append('<tbody>')
    for idx, row in df.iterrows():
        is_wbs = False

        row_class = 'class="wbs-row"' if is_wbs else ""
        html.append(f'<tr {row_class}>')

        for col in cols_to_render:
            val = row[col]
            val_str = str(val).strip() if val is not None else ""
            col_lower = col.lower()

            cell_val = ""
            cfg_key = None
            for k in column_config.keys():
                if k and k.lower() == col_lower:
                    cfg_key = k
                    break
            
            cfg = column_config[cfg_key] if cfg_key else None
            label = vietnamese_headers.get(col_lower, col)
            if cfg is not None:
                if isinstance(cfg, str):
                    label = cfg
                elif hasattr(cfg, 'label') and cfg.label:
                    label = cfg.label
                elif hasattr(cfg, 'title') and cfg.title and not callable(cfg.title):
                    label = cfg.title
            
            is_link = False
            if cfg is not None and type(cfg).__name__ == "LinkColumn":
                is_link = True

            if is_link:
                if val_str and val_str.lower() != 'none' and val_str.lower() != 'nan':
                    disp_text = "Xem tài liệu 📄"
                    if cfg and hasattr(cfg, 'display_text') and cfg.display_text:
                        disp_text = cfg.display_text
                    cell_val = f'<a href="{val_str}" target="_blank" class="btn-link">{disp_text}</a>'
                else:
                    cell_val = ""
            elif col_lower in ("tt_duyet", "tt_lap", "dat_yckt_cdt", "tt_phe_duyet", "tt_trien_khai", "trong_ngoai_hdcu", "tt_cung_ung"):
                # Clean value mapping in Vietnamese
                val_clean = val_str
                if val_str in ("Đã duyệt", "Đã lập", "Có", "Trong HĐCU", "Đã hoàn thành", "Đã ký", "Đã CU"):
                    cell_val = f'<span class="status-badge badge-green">{val_clean}</span>'
                elif val_str in ("Chưa lập", "Từ chối", "Chưa", "Ngoài HĐCU", "Từ chối duyệt", "Đóng"):
                    cell_val = f'<span class="status-badge badge-red">{val_clean}</span>'
                elif any(word in val_str for word in ("Đang", "Chờ", "Đang sửa đổi", "Đang thực hiện", "Nháp")):
                    cell_val = f'<span class="status-badge badge-yellow">{val_clean}</span>'
                else:
                    cell_val = val_clean
            elif col_lower in ("gia_tri_phat_sinh", "gia_tri_dinh_muc", "kl"):
                try:
                    num_val = float(val) if val not in ("", None) else 0.0
                    if num_val > 0:
                        if "giá trị" in label.lower() or "tỷ" in label.lower() or col_lower == "gia_tri_phat_sinh":
                            cell_val = f"<b>{num_val:,.2f} tỷ</b>"
                        else:
                            cell_val = f"{num_val:,.2f}"
                    else:
                        cell_val = ""
                except ValueError:
                    cell_val = val_str
            elif col_lower in ("muc_cham_ngay", "anh_huong_td"):
                try:
                    num_val = int(float(val)) if val not in ("", None) else 0
                    if num_val > 0:
                        cell_val = f'<span style="color: #b91c1c; font-weight: bold;">{num_val} ngày trễ</span>'
                    else:
                        cell_val = ""
                except ValueError:
                    cell_val = val_str
            else:
                cell_val = val_str

            html.append(f'<td>{cell_val}</td>')
        html.append('</tr>')

    html.append('</tbody>')
    html.append('</table>')
    html.append('</div>')

    st.markdown("".join(html), unsafe_allow_html=True)



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
    
    # Import Excel data expander
    with st.expander("📥 Nhập dữ liệu từ file Excel (Import)"):
        st.write("Tải lên file Excel để cập nhật toàn bộ cơ sở dữ liệu. Lưu ý: Thao tác này sẽ xóa sạch dữ liệu cũ và cập nhật lại theo file mới.")
        has_import_perm = check_permission('Them_HD')
        if not has_import_perm:
            st.warning("⚠️ Bạn không có quyền nhập dữ liệu từ Excel.")
        
        uploaded_file = st.file_uploader(
            "Chọn file Excel (.xlsx, .xls)", 
            type=["xlsx", "xls"], 
            disabled=not has_import_perm, 
            key="excel_file_uploader"
        )
        
        if uploaded_file is not None and has_import_perm:
            if st.button("🚀 Xác nhận Import", key="btn_confirm_import", type="primary"):
                with st.spinner("Đang xử lý dữ liệu file Excel..."):
                    try:
                        conn = database.get_connection()
                        database.seed_from_excel(conn, uploaded_file)
                        conn.close()
                        st.success("🎉 Nhập dữ liệu từ file Excel thành công!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Lỗi khi import file Excel: {e}")

    # Add new item
    with st.expander("➕ Thêm mới Hạng mục công việc"):
        with st.form("add_project_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_tt = st.text_input("Mã TT (Ví dụ: 3, 2.1, 2.2.1)")
                new_ma_bsc = st.text_input("Mã BSC *")
                new_goi_thau = st.text_input("Gói thầu (PL)")
            with c2:
                new_nhom_ct = st.selectbox("Nhóm công trình", ["Hạ tầng kỹ thuật", "Xây dựng dân dụng", "Công trình phục vụ KD"])
                new_hang_muc = st.text_input("Tên Hạng mục / Công việc *")
                new_phu_trach = st.text_input("Kỹ sư Phụ trách")
            with c3:
                new_ngan_sach = st.number_input("Ngân sách phê duyệt (tỷ)", min_value=0.0, step=0.1)
                new_ngay_bd = st.date_input("Ngày bắt đầu (Yêu cầu CĐT)", value=None)
                new_ngay_kt = st.date_input("Ngày kết thúc (Yêu cầu CĐT)", value=None)
                
            has_add_perm = check_permission('Them_HD')
            if not has_add_perm:
                st.warning("⚠️ Bạn không có quyền thêm mới hạng mục.")
            submitted = st.form_submit_button("Lưu Hạng mục", disabled=not has_add_perm)
            if submitted:
                if not has_add_perm:
                    st.error("⚠️ Bạn không có quyền thực hiện hành động này.")
                elif not new_hang_muc or not new_ma_bsc:
                    st.error("Vui lòng nhập đầy đủ Mã BSC và Tên Hạng mục / Công việc.")
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
        "🔴 A. Đầu vào CĐT",
        "🚚 B. Cung ứng & Hợp đồng",
        "⚡ D. Chốt chặn Khởi công",
        "💰 E. Ngân sách & Chi phí",
        "📊 G. Quản lý Thi công",
        "🏢 Tất cả dữ liệu"
    ]
    t1, t2, t3, t4, t5, t6 = st.tabs(tab_labels)
    
    # WBS Tree indent formatting
    def format_wbs_name(hang_muc, tt):
        return hang_muc

    # Master Column configuration
    master_column_config = {
        "TT": st.column_config.TextColumn("TT", width=60),
        "Nhóm công trình": st.column_config.TextColumn("Nhóm công trình", width=140),
        "Mã BSC": st.column_config.TextColumn("Mã BSC", width=120),
        "Hạng mục / Công việc": st.column_config.TextColumn("Hạng mục / Công việc", width=350),
        "Phụ trách": st.column_config.TextColumn("Phụ trách", width=120),
        "Ngày BD (YC CĐT)": st.column_config.DateColumn("Ngày BD (YC CĐT)", format="YYYY-MM-DD", width=120),
        "Ngày KT (YC CĐT)": st.column_config.DateColumn("Ngày KT (YC CĐT)", format="YYYY-MM-DD", width=120),
        "Ngân sách (tỷ)": st.column_config.NumberColumn("Ngân sách (tỷ)", format="%.2f tỷ", width=110),
        "KH phát hành HSTKTC": st.column_config.DateColumn("KH phát hành HSTKTC", format="YYYY-MM-DD", width=140),
        "TT HSTKTC": st.column_config.TextColumn("TT HSTKTC", width=110),
        "TT SPECS": st.column_config.TextColumn("TT SPECS", width=100),
        "TT BOQ/KL": st.column_config.TextColumn("TT BOQ/KL", width=110),
        "KH LCNT": st.column_config.DateColumn("KH LCNT", format="YYYY-MM-DD", width=110),
        "TT LCNT": st.column_config.TextColumn("TT LCNT", width=100),
        "KH Ký HĐCU": st.column_config.DateColumn("KH Ký HĐCU", format="YYYY-MM-DD", width=110),
        "TT Ký HĐCU": st.column_config.TextColumn("TT Ký HĐCU", width=110),
        "Giá trị HĐCU (tỷ)": st.column_config.NumberColumn("Giá trị HĐCU (tỷ)", format="%.2f tỷ", width=130),
        "% HĐ/NS (Tính)": st.column_config.NumberColumn("% HĐ/NS (Tính)", format="%.1f%%", width=110),
        "ĐK1 HSKT đủ": st.column_config.TextColumn("ĐK1 HSKT đủ", width=105),
        "ĐK2 HĐCU ký": st.column_config.TextColumn("ĐK2 HĐCU ký", width=105),
        "ĐK3 KHTK duyệt": st.column_config.TextColumn("ĐK3 KHTK duyệt", width=120),
        "ĐIỀU KIỆN ĐỦ": st.column_config.TextColumn("ĐIỀU KIỆN ĐỦ", width=140),
        "NGÀY KHỞI CÔNG": st.column_config.DateColumn("NGÀY KHỞI CÔNG", format="YYYY-MM-DD", width=130),
        "HS tiền KC (duyệt)": st.column_config.NumberColumn("HS tiền KC (duyệt)", format="%d bộ", width=130),
        "Lũy kế HĐ A-B": st.column_config.NumberColumn("Lũy kế HĐ A-B", format="%.2f tỷ", width=135),
        "Lũy kế Phát sinh B-B'": st.column_config.NumberColumn("Lũy kế Phát sinh B-B'", format="%.2f tỷ", width=140),
        "Tổng Chi phí Thực tế": st.column_config.NumberColumn("Tổng Chi phí Thực tế", format="%.2f tỷ", width=140),
        "Cảnh báo": st.column_config.TextColumn("Cảnh báo", width=140),
        "KH KLCV Tháng": st.column_config.ProgressColumn("KH Tháng", min_value=0.0, max_value=100.0, format="%.1f%%", width=120),
        "KQ KLCV Thực tế": st.column_config.ProgressColumn("KQ Thực tế", min_value=0.0, max_value=100.0, format="%.1f%%", width=120),
        "Đánh giá & Giải pháp Tháng": st.column_config.TextColumn("Đánh giá & Giải pháp Tháng", width=250),
        "T1 KQ": st.column_config.NumberColumn("T1 KQ", format="%.1f%%", width=85),
        "T2 KQ": st.column_config.NumberColumn("T2 KQ", format="%.1f%%", width=85),
        "T3 KQ": st.column_config.NumberColumn("T3 KQ", format="%.1f%%", width=85),
        "T4 KQ": st.column_config.NumberColumn("T4 KQ", format="%.1f%%", width=85),
        "Gói thầu (PL)": st.column_config.TextColumn("Gói thầu (PL)", width=110),
        "Ngày BD": st.column_config.DateColumn("Ngày BD", format="YYYY-MM-DD", width=120),
        "Ngày KT": st.column_config.DateColumn("Ngày KT", format="YYYY-MM-DD", width=120),
        "Khởi công": st.column_config.TextColumn("Khởi công", width=130),
    }

    # Sort and group projects by Gói thầu (PL) in a parent-child structure
    def build_parent_child_rows(proj_list):
        import re
        def parse_tt(tt_val):
            if not tt_val:
                return (999999,)
            parts = re.split(r'[.-]', str(tt_val))
            res = []
            for p_part in parts:
                p_part = p_part.strip()
                try:
                    res.append(float(p_part))
                except ValueError:
                    res.append(p_part)
            return tuple(res)
        
        # Sort projects by TT numerically/hierarchically
        sorted_projs = sorted(proj_list, key=lambda x: parse_tt(x.get('TT')))
        
        hierarchical = []
        seen_packages = set()
        for p_item in sorted_projs:
            pkg = p_item.get('Goi_thau') or "Khác"
            # Get the parent package by taking the part before the dot, e.g. PL10.13 -> PL10
            base_pkg = pkg.split('.')[0] if '.' in pkg else pkg
            nhom = p_item.get('Nhom_CT') or ""
            if base_pkg not in seen_packages:
                seen_packages.add(base_pkg)
                # Create a parent row representing the package (PL)
                parent_row = {
                    "id": f"parent_{base_pkg}",
                    "TT": base_pkg,
                    "Nhom_CT": nhom,
                    "Ma_BSC": None,
                    "Goi_thau": base_pkg,
                    "Hang_muc": f"Gói thầu {base_pkg}" + (f" ({nhom})" if nhom else ""),
                    "Phu_trach": "",
                    "Ngay_BD_YC": "",
                    "Ngay_KT_YC": "",
                    "Ngan_sach": None,
                    "is_parent": True,
                }
                # Initialize other columns to avoid errors
                for key_col in p_item.keys():
                    if key_col not in parent_row:
                        parent_row[key_col] = None
                hierarchical.append(parent_row)
            
            # Create a child row
            child_row = dict(p_item)
            child_row["is_child"] = True
            child_row["Hang_muc"] = f"    {p_item['Hang_muc']}" # Indent name with spaces
            hierarchical.append(child_row)
        return hierarchical

    projects_sorted = build_parent_child_rows(projects)

    def render_project_grid(proj_list, cols_to_show, key_suffix=""):
        col_widths_map = {
            "a": ["4%", "10%", "8%", "20%", "8%", "9%", "9%", "8%", "9%", "5%", "5%", "5%"],
            "b": ["4%", "10%", "9%", "25%", "10%", "8%", "10%", "8%", "8%", "8%"],
            "c": ["4%", "10%", "9%", "25%", "8%", "8%", "8%", "10%", "10%", "8%"],
            "d": ["4%", "11%", "9%", "26%", "8%", "10%", "10%", "12%", "10%"],
            "g": ["4%", "10%", "8%", "20%", "9%", "9%", "18%", "5%", "5%", "5%", "7%"],
            "all": ["4%", "10%", "8%", "8%", "20%", "8%", "8%", "8%", "8%", "9%", "9%"]
        }
        
        widths = col_widths_map.get(key_suffix, [f"{int(100/len(cols_to_show))}%"] * len(cols_to_show))
        html = []
        
        css = """
        <style>
            .table-container {
                width: 100%;
                max-height: 550px; /* Constrain height to force vertical scrollbar inside container */
                overflow-y: auto; /* Vertically scrollable */
                overflow-x: hidden; /* Avoid horizontal scrolling */
                border-radius: 12px;
                box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.05), 0 2px 6px -2px rgba(0, 0, 0, 0.05);
                border: 1px solid #e2e8f0;
                margin-bottom: 2rem;
                background: white;
            }
            .master-table {
                width: 100%;
                border-collapse: collapse;
                font-family: 'Inter', sans-serif;
                font-size: 0.775rem;
                color: #334155;
                table-layout: fixed;
            }
            .master-table th {
                background-color: #f8fafc !important; /* Premium light slate grey background */
                color: #475569 !important; /* Soft slate text */
                font-weight: 700;
                text-align: left;
                padding: 8px 10px;
                position: sticky;
                top: 0;
                z-index: 10;
                border-bottom: 2px solid #e2e8f0;
                font-size: 0.725rem;
                text-transform: uppercase;
                letter-spacing: 0.02em;
                word-wrap: break-word;
                white-space: normal;
                line-height: 1.25;
            }
            /* Sticky header border bottom fix when scrolling */
            .master-table th::after {
                content: '';
                position: absolute;
                left: 0;
                bottom: 0;
                width: 100%;
                border-bottom: 2px solid #e2e8f0;
            }
            .master-table td {
                padding: 8px 10px;
                border-bottom: 1px solid #f1f5f9;
                vertical-align: middle;
                word-wrap: break-word;
                white-space: normal;
                line-height: 1.35;
                color: #334155;
            }
            .master-table tr:hover {
                background-color: #f8fafc !important;
            }
            .master-table tr.wbs-row-style {
                background-color: #f8fafc !important;
                font-weight: bold;
                color: #475569;
            }
            .master-table tr.wbs-row-style td {
                font-style: italic;
                border-bottom: 1px solid #e2e8f0;
            }
            .master-badge {
                padding: 4px 8px;
                border-radius: 6px;
                font-size: 0.725rem;
                font-weight: 600;
                display: inline-block;
                text-align: center;
                line-height: 1.2;
            }
            .master-badge-green { background-color: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
            .master-badge-red { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }
            .master-badge-yellow { background-color: #fefce8; color: #a16207; border: 1px solid #fef08a; }
            .master-badge-orange { background-color: #ffedd5; color: #c2410c; border: 1px solid #fed7aa; }
            
            /* Custom progress bar */
            .html-progress-container {
                width: 100%;
                background-color: #f1f5f9;
                border-radius: 4px;
                overflow: hidden;
                height: 6px;
                margin-top: 4px;
                border: 1px solid #e2e8f0;
            }
            .html-progress-fill {
                height: 100%;
                border-radius: 4px;
            }
            .html-progress-text {
                font-size: 0.725rem;
                font-weight: 600;
                color: #64748b;
            }
        </style>
        """
        html.append(css)
        html.append('<div class="table-container">')
        html.append('<table class="master-table">')
        
        html.append('<colgroup>')
        for idx, col_name in enumerate(cols_to_show.values()):
            w = widths[idx] if idx < len(widths) else "auto"
            html.append(f'<col style="width: {w};">')
        html.append('</colgroup>')
        
        html.append('<thead><tr>')
        for col_name in cols_to_show.values():
            html.append(f'<th>{col_name}</th>')
        html.append('</tr></thead>')
        
        html.append('<tbody>')
        for p in proj_list:
            is_wbs = p.get('is_parent', False)
            tr_class = 'class="wbs-row-style"' if is_wbs else ""
            html.append(f'<tr {tr_class}>')
            
            for col_key, col_name in cols_to_show.items():
                val = ""
                
                if col_key == "Ma_BSC" and not p['Ma_BSC']:
                    val = ""
                elif col_key == "Hang_muc_formatted":
                    name_formatted = format_wbs_name(p['Hang_muc'], p['TT'])
                    leading_spaces = len(name_formatted) - len(name_formatted.lstrip(' '))
                    val = "&nbsp;" * leading_spaces + name_formatted.lstrip(' ')
                elif col_key in ("DK1_HSKT", "DK2_HDCU", "DK3_KHTK"):
                    chk = "N/A" if is_wbs else ("✔" if p[col_key] else "✘")
                    if chk == "✔":
                        val = '<span style="color: #166534; font-weight: bold; font-size: 1rem;">✔</span>'
                    elif chk == "✘":
                        val = '<span style="color: #b91c1c; font-weight: bold; font-size: 1rem;">✘</span>'
                    else:
                        val = chk
                elif col_key == "Dieu_kien_du":
                    dk_val = "---" if is_wbs else p[col_key]
                    if dk_val == "ĐỦ ĐIỀU KIỆN":
                        val = '<span class="master-badge master-badge-green">ĐỦ ĐIỀU KIỆN</span>'
                    elif dk_val == "CHƯA ĐỦ ĐK":
                        val = '<span class="master-badge master-badge-red">CHƯA ĐỦ ĐK</span>'
                    else:
                        val = dk_val
                elif col_key == "Co_Canh_bao":
                    if is_wbs:
                        val = "---"
                    else:
                        warning_val = p[col_key]
                        if warning_val == 'RED':
                            val = '<span class="master-badge master-badge-red">🔴 ĐỎ (Rủi ro)</span>'
                        elif warning_val == 'ORANGE':
                            val = '<span class="master-badge master-badge-orange">🟠 CAM (Theo dõi)</span>'
                        elif warning_val == 'YELLOW':
                            val = '<span class="master-badge master-badge-yellow">🟡 VÀNG (Chậm nhẹ)</span>'
                        else:
                            val = '<span class="master-badge master-badge-green">🟢 XANH (Bình thường)</span>'
                elif col_key in ("KH_Thang", "KQ_Thang"):
                    if is_wbs:
                        val = ""
                    else:
                        pct = p[col_key] * 100 if p[col_key] is not None else 0.0
                        bar_color = "#22c55e" if col_key == "KQ_Thang" else "#3b82f6"
                        val = f"""
                        <span class="html-progress-text">{pct:.1f}%</span>
                        <div class="html-progress-container">
                            <div class="html-progress-fill" style="width: {min(pct, 100.0)}%; background-color: {bar_color};"></div>
                        </div>
                        """
                elif col_key in ("T1_KQ", "T2_KQ", "T3_KQ", "T4_KQ", "Percent_HDCU_NS"):
                    pct = p[col_key] * 100 if p[col_key] is not None else None
                    if pct is not None:
                        if col_key == "Percent_HDCU_NS" and pct > 100.0:
                            val = f'<span style="color: #b91c1c; font-weight: bold;">{pct:.1f}%</span>'
                        else:
                            val = f'{pct:.1f}%'
                    else:
                        val = ""
                elif col_key in ("Ngan_sach", "Gia_tri_HDCU", "Luy_ke_HDCU", "Luy_ke_Phat_sinh", "Total_Cost"):
                    num = p[col_key]
                    if num is not None and num != "":
                        val = f"<b>{num:,.2f} tỷ</b>"
                    else:
                        val = ""
                elif col_key in ("TT_HSTKTC", "TT_SPECS", "TT_BOQ", "TT_LCNT", "TT_Ky_HDCU", "TT_KHTK"):
                    status_str = str(p[col_key]).strip() if p[col_key] else ""
                    if status_str in ("Đã phát hành", "Đã cấp", "Đã bàn giao", "Đã ký", "Đã CU", "Đã duyệt", "Hoàn thiện"):
                        val = f'<span class="master-badge master-badge-green">{status_str}</span>'
                    elif status_str in ("Chưa có TK", "Chưa có", "Chưa bàn giao", "Chưa LCNT", "Chưa CU", "Chưa trình"):
                        val = f'<span class="master-badge master-badge-red">{status_str}</span>'
                    elif any(word in status_str for word in ("Đang", "Chờ", "Theo đợt", "Điều chỉnh")):
                        val = f'<span class="master-badge master-badge-yellow">{status_str}</span>'
                    else:
                        val = status_str
                else:
                    item = p[col_key]
                    val = item if item is not None else ""
                    
                html.append(f'<td>{val}</td>')
            html.append('</tr>')
            
        html.append('</tbody>')
        html.append('</table>')
        html.append('</div>')
        
        st.markdown("".join(html), unsafe_allow_html=True)


    # 1. TAB A: ĐẦU VÀO CĐT
    with t1:
        cols_a = {
            "TT": "TT",
            "Nhom_CT": "Nhóm công trình",
            "Ma_BSC": "Mã BSC",
            "Hang_muc_formatted": "Hạng mục / Công việc",
            "Phu_trach": "Phụ trách",
            "Ngay_BD_YC": "Ngày BD (YC CĐT)",
            "Ngay_KT_YC": "Ngày KT (YC CĐT)",
            "Ngan_sach": "Ngân sách (tỷ)",
            "KH_phat_hanh_HSTKTC": "KH phát hành HSTKTC",
            "TT_HSTKTC": "TT HSTKTC",
            "TT_SPECS": "TT SPECS",
            "TT_BOQ": "TT BOQ/KL"
        }
        render_project_grid(projects_sorted, cols_a, "a")
        
    # 2. TAB B: CUNG ỨNG & HỢP ĐỒNG
    with t2:
        cols_b = {
            "TT": "TT",
            "Nhom_CT": "Nhóm công trình",
            "Ma_BSC": "Mã BSC",
            "Hang_muc_formatted": "Hạng mục / Công việc",
            "KH_LCNT": "KH LCNT",
            "TT_LCNT": "TT LCNT",
            "KH_Ky_HDCU": "KH Ký HĐCU",
            "TT_Ky_HDCU": "TT Ký HĐCU",
            "Gia_tri_HDCU": "Giá trị HĐCU (tỷ)",
            "Percent_HDCU_NS": "% HĐ/NS (Tính)"
        }
        render_project_grid(projects_sorted, cols_b, "b")

    # 3. TAB D: CHỐT CHẶN KHỞI CÔNG
    with t3:
        cols_c = {
            "TT": "TT",
            "Nhom_CT": "Nhóm công trình",
            "Ma_BSC": "Mã BSC",
            "Hang_muc_formatted": "Hạng mục / Công việc",
            "DK1_HSKT": "ĐK1 HSKT đủ",
            "DK2_HDCU": "ĐK2 HĐCU ký",
            "DK3_KHTK": "ĐK3 KHTK duyệt",
            "Dieu_kien_du": "ĐIỀU KIỆN ĐỦ",
            "Ngay_BD_Khoi_Cong": "NGÀY KHỞI CÔNG",
            "Approved_HSo_Count": "HS tiền KC (duyệt)"
        }
        render_project_grid(projects_sorted, cols_c, "c")

    # 4. TAB E: NGÂN SÁCH & CHI PHÍ
    with t4:
        cols_d = {
            "TT": "TT",
            "Nhom_CT": "Nhóm công trình",
            "Ma_BSC": "Mã BSC",
            "Hang_muc_formatted": "Hạng mục / Công việc",
            "Ngan_sach": "Ngân sách (tỷ)",
            "Luy_ke_HDCU": "Lũy kế HĐ A-B",
            "Luy_ke_Phat_sinh": "Lũy kế Phát sinh B-B'",
            "Total_Cost": "Tổng Chi phí Thực tế",
            "Co_Canh_bao": "Cảnh báo"
        }
        render_project_grid(projects_sorted, cols_d, "d")

    # 5. TAB G: QUẢN LÝ THI CÔNG
    with t5:
        cols_g = {
            "TT": "TT",
            "Nhom_CT": "Nhóm công trình",
            "Ma_BSC": "Mã BSC",
            "Hang_muc_formatted": "Hạng mục / Công việc",
            "KH_Thang": "KH KLCV Tháng",
            "KQ_Thang": "KQ KLCV Thực tế",
            "Danh_gia_Thang": "Đánh giá & Giải pháp Tháng",
            "T1_KQ": "T1 KQ",
            "T2_KQ": "T2 KQ",
            "T3_KQ": "T3 KQ",
            "T4_KQ": "T4 KQ"
        }
        render_project_grid(projects_sorted, cols_g, "g")

    # 6. TAB ALL (TẤT CẢ DỮ LIỆU)
    with t6:
        cols_all = {
            "TT": "TT",
            "Nhom_CT": "Nhóm công trình",
            "Ma_BSC": "Mã BSC",
            "Goi_thau": "Gói thầu (PL)",
            "Hang_muc_formatted": "Hạng mục / Công việc",
            "Phu_trach": "Phụ trách",
            "Ngay_BD_YC": "Ngày BD",
            "Ngay_KT_YC": "Ngày KT",
            "Ngan_sach": "Ngân sách (tỷ)",
            "Dieu_kien_du": "Khởi công",
            "Co_Canh_bao": "Cảnh báo"
        }
        render_project_grid(projects_sorted, cols_all, "all")

    # Unified Action layout below the tabs (super clean and non-repeating)
    st.write("---")
    st.write("⚙️ *Hành động nhanh cho Hạng mục công việc:*")
    
    has_edit_perm = check_permission('Sua')
    has_delete_perm = check_permission('Xoa_HD')
    if not has_edit_perm or not has_delete_perm:
        missing = []
        if not has_edit_perm: missing.append("chỉnh sửa")
        if not has_delete_perm: missing.append("xóa")
        st.warning(f"⚠️ Bạn không có quyền { ' và '.join(missing) } hạng mục.")

    cols = st.columns(4)
    with cols[0]:
        p_to_edit = st.selectbox("Chọn hạng mục chỉnh sửa tiến trình", [f"{p['id']} - {p['Hang_muc'].strip()}" for p in projects_sorted if not p.get('is_parent')], key="sel_edit_unified")
    
    with cols[1]:
        if st.button("✏️ Cập nhật tiến trình", key="btn_edit_unified", disabled=not has_edit_perm):
            if not has_edit_perm:
                st.error("⚠️ Bạn không có quyền thực hiện hành động này.")
            else:
                p_id = int(p_to_edit.split(" - ")[0])
                st.session_state['edit_project_id'] = p_id
                st.session_state['show_edit_form'] = True
            
    with cols[2]:
        if st.button("🗑️ Xóa hạng mục", key="btn_delete_unified", disabled=not has_delete_perm):
            if not has_delete_perm:
                st.error("⚠️ Bạn không có quyền thực hiện hành động này.")
            else:
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

            has_edit_perm = check_permission('Sua')
            if not has_edit_perm:
                st.warning("⚠️ Bạn không có quyền chỉnh sửa hạng mục này.")
            submitted_edit = st.form_submit_button("Lưu thay đổi", disabled=not has_edit_perm)
            if submitted_edit:
                if not has_edit_perm:
                    st.error("⚠️ Bạn không có quyền thực hiện hành động này.")
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
                
            has_add_perm = check_permission('Them_HD')
            if not has_add_perm:
                st.warning("⚠️ Bạn không có quyền thêm mới hồ sơ.")
            submitted_hso = st.form_submit_button("Lưu Hồ sơ", disabled=not has_add_perm)
            if submitted_hso:
                if not has_add_perm:
                    st.error("⚠️ Bạn không có quyền thực hiện hành động này.")
                elif not h_ten:
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
    
    hso_column_config = {
        "id": None,
        "Ma_BSC": st.column_config.TextColumn("Mã BSC", width=120),
        "Hang_muc": st.column_config.TextColumn("Hạng mục", width=200),
        "Loai_ho_so": st.column_config.TextColumn("Loại hồ sơ", width=110),
        "Ten_san_pham": st.column_config.TextColumn("Tên hồ sơ / văn bản", width=300),
        "Link_luu_tru": st.column_config.LinkColumn("Link lưu trữ", width=180, display_text="Xem tài liệu 📄"),
        "Ngay_HT": st.column_config.DateColumn("Ngày hoàn thành", format="YYYY-MM-DD", width=130),
        "Nguoi_lap": st.column_config.TextColumn("Người lập", width=120),
        "Nguoi_duyet": st.column_config.TextColumn("Người duyệt", width=120),
        "TT_duyet": st.column_config.TextColumn("Trạng thái duyệt", width=130)
    }
    
    render_dataframe_html(df_hso, hso_column_config, "hso_tienkc")

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
                
            has_add_perm = check_permission('Them_HD')
            if not has_add_perm:
                st.warning("⚠️ Bạn không có quyền thêm mới kế hoạch.")
            submitted_kh = st.form_submit_button("Lưu Kế hoạch", disabled=not has_add_perm)
            if submitted_kh:
                if not has_add_perm:
                    st.error("⚠️ Bạn không có quyền thực hiện hành động này.")
                elif not kh_nd:
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
    df_kh = pd.read_sql_query("SELECT id, Ma_BSC, Hang_muc, Thang, Loai_tai_lieu, Noi_dung_chinh, Dat_YCKT_CDT, Link_tai_lieu, TT_lap, TT_duyet, Nguoi_lap, Nguoi_duyet, Ngay_duyet FROM kh_thang_tuan", conn)
    conn.close()
    
    kh_column_config = {
        "id": None,
        "Ma_BSC": st.column_config.TextColumn("Mã BSC", width=120),
        "Hang_muc": st.column_config.TextColumn("Hạng mục", width=200),
        "Thang": st.column_config.TextColumn("Tháng", width=90),
        "Loai_tai_lieu": st.column_config.TextColumn("Loại tài liệu", width=180),
        "Noi_dung_chinh": st.column_config.TextColumn("Nội dung chính", width=280),
        "Dat_YCKT_CDT": st.column_config.TextColumn("Đạt YCKT CĐT?", width=130),
        "Link_tai_lieu": st.column_config.LinkColumn("Link tài liệu", width=150, display_text="Xem kế hoạch 📄"),
        "TT_lap": st.column_config.TextColumn("TT Lập", width=100),
        "TT_duyet": st.column_config.TextColumn("TT Duyệt", width=110),
        "Nguoi_lap": st.column_config.TextColumn("Người lập", width=120),
        "Nguoi_duyet": st.column_config.TextColumn("Người duyệt", width=120),
        "Ngay_duyet": st.column_config.DateColumn("Ngày duyệt", format="YYYY-MM-DD", width=120)
    }
    
    render_dataframe_html(df_kh, kh_column_config, "kh_thang_tuan")

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
                
            has_add_perm = check_permission('Them_HD')
            if not has_add_perm:
                st.warning("⚠️ Bạn không có quyền báo cáo phát sinh.")
            submitted_ps = st.form_submit_button("Lưu Đệ trình", disabled=not has_add_perm)
            if submitted_ps:
                if not has_add_perm:
                    st.error("⚠️ Bạn không có quyền thực hiện hành động này.")
                elif not ps_ma:
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
    df_ps = pd.read_sql_query("SELECT id, Ma_PS, Ma_BSC, Hang_muc, Ngay_PS, Loai, Mo_ta, Nguyen_nhan, De_xuat_xu_ly, Gia_tri_phat_sinh, Anh_huong_TD, Link_ho_so, TT_Phe_duyet, Nguoi_duyet, Ngay_duyet, Noi_dung_dieu_chinh, Ghi_chu FROM phat_sinh", conn)
    conn.close()
    
    ps_column_config = {
        "id": None,
        "Ma_PS": st.column_config.TextColumn("Mã PS", width=110),
        "Ma_BSC": st.column_config.TextColumn("Mã BSC", width=120),
        "Hang_muc": st.column_config.TextColumn("Hạng mục", width=200),
        "Ngay_PS": st.column_config.DateColumn("Ngày PS", format="YYYY-MM-DD", width=110),
        "Loai": st.column_config.TextColumn("Phân loại", width=160),
        "Mo_ta": st.column_config.TextColumn("Mô tả chi tiết", width=250),
        "Nguyen_nhan": st.column_config.TextColumn("Nguyên nhân", width=200),
        "De_xuat_xu_ly": st.column_config.TextColumn("Đề xuất xử lý", width=200),
        "Gia_tri_phat_sinh": st.column_config.NumberColumn("Giá trị PS (tỷ)", format="%.2f tỷ", width=120),
        "Anh_huong_TD": st.column_config.NumberColumn("Ảnh hưởng TD (ngày)", format="%d ngày", width=140),
        "Link_ho_so": st.column_config.LinkColumn("Link hồ sơ", width=150, display_text="Xem hồ sơ phát sinh 📄"),
        "TT_Phe_duyet": st.column_config.TextColumn("TT Phê duyệt", width=125),
        "Nguoi_duyet": st.column_config.TextColumn("Người duyệt", width=120),
        "Ngay_duyet": st.column_config.DateColumn("Ngày duyệt", format="YYYY-MM-DD", width=110),
        "Noi_dung_dieu_chinh": st.column_config.TextColumn("Nội dung điều chỉnh", width=200),
        "Ghi_chu": st.column_config.TextColumn("Ghi chú", width=150)
    }
    
    render_dataframe_html(df_ps, ps_column_config, "phat_sinh")

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
                
            has_add_perm = check_permission('Them_HD')
            if not has_add_perm:
                st.warning("⚠️ Bạn không có quyền đệ trình yêu cầu cung ứng.")
            submitted_cu = st.form_submit_button("Lưu Yêu cầu", disabled=not has_add_perm)
            if submitted_cu:
                if not has_add_perm:
                    st.error("⚠️ Bạn không có quyền thực hiện hành động này.")
                elif not cu_ma or not cu_vt:
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
    df_cu = pd.read_sql_query("SELECT id, Ma_YC, Ma_BSC, Hang_muc, Ngay_YC, Loai_YC, Vat_tu_thiet_bi, Noi_dung_yeu_cau, KL, DVT, Gia_tri_phat_sinh, Trong_Ngoai_HDCU, Link_ho_so, TT_Phe_duyet, Nguoi_duyet, Ngay_can, TT_cung_ung, Ghi_chu FROM cu_dac_thu", conn)
    conn.close()
    
    cu_column_config = {
        "id": None,
        "Ma_YC": st.column_config.TextColumn("Mã YC", width=110),
        "Ma_BSC": st.column_config.TextColumn("Mã BSC", width=120),
        "Hang_muc": st.column_config.TextColumn("Hạng mục", width=200),
        "Ngay_YC": st.column_config.DateColumn("Ngày yêu cầu", format="YYYY-MM-DD", width=120),
        "Loai_YC": st.column_config.TextColumn("Tính chất", width=110),
        "Vat_tu_thiet_bi": st.column_config.TextColumn("Vật tư / Thiết bị", width=200),
        "Noi_dung_yeu_cau": st.column_config.TextColumn("Mô tả / Lý do", width=220),
        "KL": st.column_config.NumberColumn("Khối lượng", format="%.2f", width=110),
        "DVT": st.column_config.TextColumn("ĐVT", width=80),
        "Gia_tri_phat_sinh": st.column_config.NumberColumn("Giá trị (tỷ)", format="%.2f tỷ", width=110),
        "Trong_Ngoai_HDCU": st.column_config.TextColumn("Phạm vi HĐ", width=130),
        "Link_ho_so": st.column_config.LinkColumn("Link hồ sơ", width=140, display_text="Xem tài liệu kỹ thuật 📄"),
        "TT_Phe_duyet": st.column_config.TextColumn("TT Phê duyệt", width=120),
        "Nguoi_duyet": st.column_config.TextColumn("Người duyệt", width=120),
        "Ngay_can": st.column_config.DateColumn("Ngày cần vật tư", format="YYYY-MM-DD", width=120),
        "TT_cung_ung": st.column_config.TextColumn("TT Cung ứng", width=120),
        "Ghi_chu": st.column_config.TextColumn("Ghi chú", width=150)
    }
    
    render_dataframe_html(df_cu, cu_column_config, "cu_dac_thu")

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
                
            has_add_perm = check_permission('Them_HD')
            if not has_add_perm:
                st.warning("⚠️ Bạn không có quyền thiết lập phương án bù tiến độ.")
            submitted_bu = st.form_submit_button("Lưu Phương án", disabled=not has_add_perm)
            if submitted_bu:
                if not has_add_perm:
                    st.error("⚠️ Bạn không có quyền thực hiện hành động này.")
                elif not bu_pa:
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
    df_bu = pd.read_sql_query("SELECT id, Ma_BSC, Hang_muc, Ngay_phat_hien, Muc_cham_ngay, Nguyen_nhan, Phuong_an, Chi_tiet_giai_phap, Moc_cam_ket_HT, Link_phuong_an, TT_duyet, Nguoi_duyet, KQ_thuc_hien_bu, TT_Trien_khai, Ghi_chu FROM bu_tien_do", conn)
    conn.close()
    
    bu_column_config = {
        "id": None,
        "Ma_BSC": st.column_config.TextColumn("Mã BSC", width=120),
        "Hang_muc": st.column_config.TextColumn("Hạng mục", width=200),
        "Ngay_phat_hien": st.column_config.DateColumn("Ngày phát hiện chậm", format="YYYY-MM-DD", width=150),
        "Muc_cham_ngay": st.column_config.NumberColumn("Số ngày trễ", format="%d ngày trễ", width=120),
        "Nguyen_nhan": st.column_config.TextColumn("Nguyên nhân chậm trễ", width=220),
        "Phuong_an": st.column_config.TextColumn("Giải pháp bù", width=220),
        "Chi_tiet_giai_phap": st.column_config.TextColumn("Kế hoạch chi tiết", width=250),
        "Moc_cam_ket_HT": st.column_config.DateColumn("Hạn chót cam kết", format="YYYY-MM-DD", width=140),
        "Link_phuong_an": st.column_config.LinkColumn("Link phương án", width=140, display_text="Xem phương án bù 📄"),
        "TT_duyet": st.column_config.TextColumn("TT Duyệt", width=110),
        "Nguoi_duyet": st.column_config.TextColumn("Người duyệt", width=120),
        "KQ_thuc_hien_bu": st.column_config.TextColumn("Đánh giá kết quả bù", width=200),
        "TT_Trien_khai": st.column_config.TextColumn("TT Triển khai", width=130),
        "Ghi_chu": st.column_config.TextColumn("Ghi chú", width=150)
    }
    
    render_dataframe_html(df_bu, bu_column_config, "bu_tien_do")
# --- 8. AI ASSISTANT VIEW ---
elif choice == "🤖 Trợ lý AI Thông minh":
    st.title("🤖 Trợ lý AI Phân tích Báo cáo Xây dựng")
    
    st.info(
        "Nhập báo cáo tiến độ tuần bằng ngôn ngữ tự nhiên từ công trường. Trợ lý AI sẽ: \n"
        "1. Tự động đối chiếu Mã BSC và phân tích nội dung báo cáo.\n"
        "2. Tự động cập nhật tiến độ tuần tương ứng vào Bảng Master chính.\n"
        "3. Tự động chèn hồ sơ, kế hoạch, phát sinh, cung ứng đặc thù, hoặc phương án bù tiến độ vào các sổ 01 - 05 tương ứng."
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
                    
                    actions = parsed_json.get("actions", [])
                    if not actions:
                        st.info("🤖 Không tìm thấy hành động đồng bộ dữ liệu nào phù hợp từ báo cáo thô.")
                    else:
                        conn = database.get_connection()
                        cursor = conn.cursor()
                        
                        for act in actions:
                            a_type = act.get("type")
                            ma_bsc_matched = act.get("ma_bsc")
                            
                            # Skip if Ma_BSC is not found
                            if ma_bsc_matched:
                                # Verify project exists
                                cursor.execute("SELECT Hang_muc FROM master_bang_tonghop WHERE Ma_BSC = ?", (ma_bsc_matched,))
                                res_p = cursor.fetchone()
                                if not res_p:
                                    st.warning(f"⚠️ Mã BSC '{ma_bsc_matched}' không tồn tại trong Bảng Tổng hợp Master. Bỏ qua hành động này.")
                                    continue
                                hang_muc_matched = res_p[0]
                                
                                if a_type == "update_master_progress":
                                    week_index = act.get("week_index")
                                    week_kq = act.get("week_kq")
                                    week_danh_gia = act.get("week_danh_gia")
                                    if week_index in [1, 2, 3, 4]:
                                        kq_col = f"T{week_index}_KQ"
                                        dg_col = f"T{week_index}_Danh_gia"
                                        cursor.execute(f"""
                                            UPDATE master_bang_tonghop 
                                            SET {kq_col} = ?, {dg_col} = ? 
                                            WHERE Ma_BSC = ?
                                        """, (week_kq, week_danh_gia, ma_bsc_matched))
                                        st.write(f"✅ Đã tự động cập nhật tiến độ Tuần {week_index} của dự án '{hang_muc_matched}' ({ma_bsc_matched}) đạt {week_kq*100:.1f}%.")
                                
                                elif a_type == "insert_hso_tienkc":
                                    cursor.execute("""
                                        INSERT INTO hso_tienkc (Ma_BSC, Hang_muc, Loai_ho_so, Ten_san_pham, Link_luu_tru, Ngay_HT, Nguoi_lap, Nguoi_duyet, TT_duyet)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        ma_bsc_matched, hang_muc_matched,
                                        act.get("loai_ho_so", "HSTKTC"),
                                        act.get("ten_san_pham", "Tài liệu tự động từ AI"),
                                        act.get("link_luu_tru"),
                                        act.get("nguoi_lap", "AI Assistant"),
                                        act.get("nguoi_duyet"),
                                        act.get("tt_duyet", "Đã duyệt")
                                    ))
                                    st.write(f"✅ Đã tự động thêm Hồ sơ mới: '{act.get('ten_san_pham')}' cho dự án '{hang_muc_matched}'.")
                                
                                elif a_type == "insert_kh_thang_tuan":
                                    cursor.execute("""
                                        INSERT INTO kh_thang_tuan (Ma_BSC, Hang_muc, Thang, Loai_tai_lieu, Noi_dung_chinh, Dat_YCKT_CDT, Link_tai_lieu, TT_lap, TT_duyet, Nguoi_lap, Nguoi_duyet, Ngay_duyet)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        ma_bsc_matched, hang_muc_matched,
                                        act.get("thang", "06/2026"),
                                        act.get("loai_tai_lieu", "Biện pháp thi công"),
                                        act.get("noi_dung_chinh", "Tài liệu tự động từ AI"),
                                        act.get("dat_yckt_cdt", "Có"),
                                        act.get("link_tai_lieu"),
                                        act.get("tt_lap", "Đã lập"),
                                        act.get("tt_duyet", "Đã duyệt"),
                                        act.get("nguoi_lap", "AI Assistant"),
                                        act.get("nguoi_duyet"),
                                        datetime.date.today().strftime('%Y-%m-%d')
                                    ))
                                    st.write(f"✅ Đã tự động lập Kế hoạch đệ trình: '{act.get('noi_dung_chinh')}' cho dự án '{hang_muc_matched}'.")
                                
                                elif a_type == "insert_phat_sinh":
                                    cursor.execute("""
                                        INSERT INTO phat_sinh (Ma_PS, Ma_BSC, Hang_muc, Ngay_PS, Loai, Mo_ta, Nguyen_nhan, De_xuat_xu_ly, Gia_tri_phat_sinh, Anh_huong_TD, Link_ho_so, TT_Phe_duyet, Nguoi_duyet)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        act.get("ma_ps", f"PS.AI.{datetime.date.today().strftime('%m%d%H%M')}"),
                                        ma_bsc_matched, hang_muc_matched,
                                        datetime.date.today().strftime('%Y-%m-%d'),
                                        act.get("loai", "Khác"),
                                        act.get("mo_ta"),
                                        act.get("nguyen_nhan"),
                                        act.get("de_xuat_xu_ly"),
                                        act.get("gia_tri_phat_sinh", 0.0),
                                        act.get("anh_huong_td", 0),
                                        act.get("link_ho_so"),
                                        act.get("tt_phe_duyet", "Chờ duyệt"),
                                        act.get("nguoi_duyet")
                                    ))
                                    st.write(f"✅ Đã tự động báo cáo Phát sinh: '{act.get('ma_ps')}' trị giá {act.get('gia_tri_phat_sinh', 0.0)} tỷ cho dự án '{hang_muc_matched}'.")
                                
                                elif a_type == "insert_cu_dac_thu":
                                    cursor.execute("""
                                        INSERT INTO cu_dac_thu (Ma_YC, Ma_BSC, Hang_muc, Ngay_YC, Loai_YC, Vat_tu_thiet_bi, Noi_dung_yeu_cau, KL, DVT, Gia_tri_phat_sinh, Trong_Ngoai_HDCU, Link_ho_so, TT_Phe_duyet, Nguoi_duyet)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        act.get("ma_yc", f"YC.AI.{datetime.date.today().strftime('%m%d%H%M')}"),
                                        ma_bsc_matched, hang_muc_matched,
                                        datetime.date.today().strftime('%Y-%m-%d'),
                                        act.get("loai_yc", "Đột xuất"),
                                        act.get("vat_tu_thiet_bi", "Vật tư"),
                                        act.get("noi_dung_yeu_cau"),
                                        act.get("kl", 1.0),
                                        act.get("dvt", "Bộ"),
                                        act.get("gia_tri_phat_sinh", 0.0),
                                        act.get("trong_ngoai_hdcu", "Ngoài HĐCU"),
                                        act.get("link_ho_so"),
                                        act.get("tt_phe_duyet", "Chờ duyệt"),
                                        act.get("nguoi_duyet")
                                    ))
                                    st.write(f"✅ Đã tự động lập yêu cầu Cung ứng đặc thù: '{act.get('vat_tu_thiet_bi')}' cho dự án '{hang_muc_matched}'.")
                                
                                elif a_type == "insert_bu_tien_do":
                                    cursor.execute("""
                                        INSERT INTO bu_tien_do (Ma_BSC, Hang_muc, Ngay_phat_hien, Muc_cham_ngay, Nguyen_nhan, Phuong_an, Chi_tiet_giai_phap, Moc_cam_ket_HT, Link_phuong_an, TT_duyet, Nguoi_duyet, KQ_thuc_hien_bu, TT_Trien_khai)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        ma_bsc_matched, hang_muc_matched,
                                        datetime.date.today().strftime('%Y-%m-%d'),
                                        act.get("muc_cham_ngay", 5.0),
                                        act.get("nguyen_nhan"),
                                        act.get("phuong_an", "Giải pháp bù tiến độ"),
                                        act.get("chi_tiet_giai_phap"),
                                        act.get("moc_cam_ket_ht"),
                                        act.get("link_phuong_an"),
                                        act.get("tt_duyet", "Chờ duyệt"),
                                        act.get("nguoi_duyet"),
                                        act.get("kq_thuc_hien_bu"),
                                        act.get("tt_trien_khai", "Đang thực hiện")
                                    ))
                                    st.write(f"✅ Đã tự động thiết lập Phương án bù tiến độ (Sổ 05) cho dự án '{hang_muc_matched}' ở trạng thái '{act.get('tt_trien_khai', 'Đang thực hiện')}'.")
                        
                        conn.commit()
                        conn.close()
                        st.success("🎉 Hệ thống đã được đồng bộ dữ liệu tự động thành công!")
                except Exception as ex:
                    st.error(f"Lỗi: {ex}")

# --- 9. PERSONNEL & PERMISSIONS MANAGEMENT ---
elif choice == "👥 Quản lý Nhân sự":
    st.write("## 👥 Quản lý Danh sách Nhân sự & Phân quyền")
    
    conn = database.get_connection()
    df_ns = pd.read_sql_query("SELECT id, Ma_NV, Ho_Ten, Chuc_Vu, Vai_Tro, Email, Them_HD, Sua, Xoa_HD, Sua_CDT_BD, Cap_Nhat_CDT FROM nhan_su", conn)
    conn.close()
    
    # 1. Filter dropdown matching your screen
    positions = sorted(list(set(df_ns['Chuc_Vu'].dropna().tolist())))
    filter_options = ["Tất cả Nhân sự"] + positions
    
    c_f1, c_f2 = st.columns([8, 2])
    with c_f1:
        sel_filter = st.selectbox("Lọc theo loại:", filter_options, key="sel_filter_personnel")
    
    if sel_filter != "Tất cả Nhân sự":
        df_ns = df_ns[df_ns['Chuc_Vu'] == sel_filter]
        
    # Render personnel table
    def render_personnel_html(df):
        html = []
        css = """
        <style>
            .ns-container {
                width: 100%;
                overflow-x: hidden;
                border-radius: 12px;
                box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.05), 0 2px 6px -2px rgba(0, 0, 0, 0.05);
                border: 1px solid #e2e8f0;
                margin-bottom: 2rem;
                background: white;
            }
            .ns-table {
                width: 100%;
                border-collapse: collapse;
                font-family: 'Inter', sans-serif;
                font-size: 0.775rem;
                color: #334155;
                table-layout: fixed;
            }
            .ns-table th {
                background-color: #f8fafc !important;
                color: #475569 !important;
                font-weight: 700;
                text-align: left;
                padding: 8px 10px;
                position: sticky;
                top: 0;
                z-index: 10;
                border-bottom: 2px solid #e2e8f0;
                font-size: 0.725rem;
                text-transform: uppercase;
                letter-spacing: 0.02em;
                word-wrap: break-word;
                white-space: normal;
                line-height: 1.25;
            }
            .ns-table th::after {
                content: '';
                position: absolute;
                left: 0;
                bottom: 0;
                width: 100%;
                border-bottom: 2px solid #e2e8f0;
            }
            .ns-table td {
                padding: 8px 10px;
                border-bottom: 1px solid #f1f5f9;
                vertical-align: middle;
                word-wrap: break-word;
                white-space: normal;
                line-height: 1.35;
            }
            .ns-table tr:hover {
                background-color: #f8fafc !important;
            }
            .ns-badge-co {
                color: #15803d;
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }
            .ns-badge-khong {
                color: #b91c1c;
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }
            .ns-btn-sua {
                background-color: #fef9c3;
                color: #854d0e;
                border: 1px solid #fef08a;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.725rem;
                font-weight: 600;
                display: inline-block;
            }
            .ns-btn-xoa {
                background-color: #fee2e2;
                color: #b91c1c;
                border: 1px solid #fca5a5;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.725rem;
                font-weight: 600;
                display: inline-block;
            }
        </style>
        """
        html.append(css)
        html.append('<div class="ns-container">')
        html.append('<table class="ns-table">')
        
        # Colgroup for widths
        html.append('<colgroup>')
        widths = ["6%", "14%", "10%", "8%", "18%", "8%", "7%", "8%", "8%", "8%", "11%"]
        for w in widths:
            html.append(f'<col style="width: {w};">')
        html.append('</colgroup>')
        
        # Headers
        html.append('<thead><tr>')
        headers = ["Mã NV", "Họ & Tên", "Chức vụ", "Vai trò", "Email", "Thêm HĐ", "Sửa", "Xóa HĐ", "Sửa CĐT BĐ", "Cập nhật CĐT", "Thao tác"]
        for h in headers:
            html.append(f'<th>{h}</th>')
        html.append('</tr></thead>')
        
        # Body
        html.append('<tbody>')
        for idx, row in df.iterrows():
            html.append('<tr>')
            html.append(f'<td style="color: #6366f1; font-weight: 700;">{row["Ma_NV"]}</td>')
            html.append(f'<td><b>{row["Ho_Ten"]}</b></td>')
            html.append(f'<td style="color: #64748b;">{row["Chuc_Vu"]}</td>')
            html.append(f'<td style="color: #64748b;">{row["Vai_Tro"]}</td>')
            html.append(f'<td style="color: #64748b; font-size: 0.75rem;">{row["Email"]}</td>')
            
            # Permissions
            perm_cols = ["Them_HD", "Sua", "Xoa_HD", "Sua_CDT_BD", "Cap_Nhat_CDT"]
            for col in perm_cols:
                if row[col] == 1:
                    html.append('<td><span class="ns-badge-co">🟢 Có</span></td>')
                else:
                    html.append('<td><span class="ns-badge-khong">🔴 Không</span></td>')
                    
            # Actions
            html.append(f'<td><span class="ns-btn-sua">Sửa</span> <span class="ns-btn-xoa">Xóa</span></td>')
            html.append('</tr>')
            
        html.append('</tbody>')
        html.append('</table>')
        html.append('</div>')
        
        return "".join(html)

    # Render HTML Personnel table
    st.markdown(render_personnel_html(df_ns), unsafe_allow_html=True)
    
    st.write("---")
    st.write("⚙️ *Hành động nhanh cho Danh sách Nhân sự:*")
    
    # 2. Add New Personnel
    with st.expander("➕ Thêm Nhân viên mới"):
        with st.form("add_ns_form"):
            c1, c2 = st.columns(2)
            with c1:
                add_ma = st.text_input("Mã Nhân viên (Mã NV) *")
                add_ten = st.text_input("Họ & Tên *")
                add_chuc = st.text_input("Chức vụ")
                add_vai = st.text_input("Vai trò")
                add_email = st.text_input("Email")
            with c2:
                st.write("**Phân quyền chức năng:**")
                add_them_hd = st.checkbox("Thêm HĐ", value=False)
                add_sua = st.checkbox("Sửa", value=False)
                add_xoa_hd = st.checkbox("Xóa HĐ", value=False)
                add_sua_cdt = st.checkbox("Sửa CĐT BĐ", value=False)
                add_cap_nhat = st.checkbox("Cập nhật CĐT", value=False)
                
            has_add_perm = check_permission('Them_HD')
            if not has_add_perm:
                st.warning("⚠️ Bạn không có quyền thêm mới nhân sự.")
            btn_add_ns = st.form_submit_button("Lưu nhân sự", disabled=not has_add_perm)
            if btn_add_ns:
                if not has_add_perm:
                    st.error("⚠️ Bạn không có quyền thực hiện hành động này.")
                elif not add_ma or not add_ten:
                    st.error("Vui lòng nhập Mã NV và Họ & Tên.")
                else:
                    conn = database.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO nhan_su (Ma_NV, Ho_Ten, Chuc_Vu, Vai_Tro, Email, Them_HD, Sua, Xoa_HD, Sua_CDT_BD, Cap_Nhat_CDT)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (add_ma, add_ten, add_chuc, add_vai, add_email, 
                          1 if add_them_hd else 0, 1 if add_sua else 0, 1 if add_xoa_hd else 0, 
                          1 if add_sua_cdt else 0, 1 if add_cap_nhat else 0))
                    conn.commit()
                    conn.close()
                    st.success("Thêm nhân sự mới thành công!")
                    st.rerun()
                    
    # 3. Edit Personnel
    with st.expander("✏️ Chỉnh sửa thông tin & Phân quyền"):
        ns_list = [f"{row['id']} - {row['Ho_Ten']} (Mã NV: {row['Ma_NV']})" for idx, row in df_ns.iterrows()]
        if ns_list:
            sel_ns = st.selectbox("Chọn nhân viên cần chỉnh sửa:", ns_list, key="sel_edit_ns")
            sel_id = int(sel_ns.split(" - ")[0])
            
            # Fetch employee current info
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM nhan_su WHERE id = ?", (sel_id,))
            row_edit = cursor.fetchone()
            conn.close()
            
            if row_edit:
                with st.form("edit_ns_form"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        edit_ma = st.text_input("Mã Nhân viên *", value=row_edit['Ma_NV'] or "")
                        edit_ten = st.text_input("Họ & Tên *", value=row_edit['Ho_Ten'] or "")
                        edit_chuc = st.text_input("Chức vụ", value=row_edit['Chuc_Vu'] or "")
                        edit_vai = st.text_input("Vai trò", value=row_edit['Vai_Tro'] or "")
                        edit_email = st.text_input("Email", value=row_edit['Email'] or "")
                    with ec2:
                        st.write("**Chỉnh sửa quyền:**")
                        edit_them_hd = st.checkbox("Thêm HĐ", value=(row_edit['Them_HD'] == 1))
                        edit_sua = st.checkbox("Sửa", value=(row_edit['Sua'] == 1))
                        edit_xoa_hd = st.checkbox("Xóa HĐ", value=(row_edit['Xoa_HD'] == 1))
                        edit_sua_cdt = st.checkbox("Sửa CĐT BĐ", value=(row_edit['Sua_CDT_BD'] == 1))
                        edit_cap_nhat = st.checkbox("Cập nhật CĐT", value=(row_edit['Cap_Nhat_CDT'] == 1))
                        
                    has_edit_perm = check_permission('Sua')
                    if not has_edit_perm:
                        st.warning("⚠️ Bạn không có quyền chỉnh sửa thông tin nhân sự.")
                    btn_edit_ns = st.form_submit_button("Lưu thay đổi", disabled=not has_edit_perm)
                    if btn_edit_ns:
                        if not has_edit_perm:
                            st.error("⚠️ Bạn không có quyền thực hiện hành động này.")
                        elif not edit_ma or not edit_ten:
                            st.error("Mã NV và Họ & Tên không được bỏ trống.")
                        else:
                            conn = database.get_connection()
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE nhan_su
                                SET Ma_NV = ?, Ho_Ten = ?, Chuc_Vu = ?, Vai_Tro = ?, Email = ?,
                                    Them_HD = ?, Sua = ?, Xoa_HD = ?, Sua_CDT_BD = ?, Cap_Nhat_CDT = ?
                                WHERE id = ?
                            """, (edit_ma, edit_ten, edit_chuc, edit_vai, edit_email,
                                  1 if edit_them_hd else 0, 1 if edit_sua else 0, 1 if edit_xoa_hd else 0,
                                  1 if edit_sua_cdt else 0, 1 if edit_cap_nhat else 0, sel_id))
                            conn.commit()
                            conn.close()
                            st.success("Cập nhật thông tin nhân viên thành công!")
                            st.rerun()
                            
    # 4. Delete Personnel
    with st.expander("🗑️ Xóa nhân viên"):
        ns_list_del = [f"{row['id']} - {row['Ho_Ten']} (Mã NV: {row['Ma_NV']})" for idx, row in df_ns.iterrows()]
        if ns_list_del:
            sel_ns_del = st.selectbox("Chọn nhân viên cần xóa:", ns_list_del, key="sel_del_ns")
            sel_id_del = int(sel_ns_del.split(" - ")[0])
            
            has_delete_perm = check_permission('Xoa_HD')
            if not has_delete_perm:
                st.warning("⚠️ Bạn không có quyền xóa nhân sự.")
            if st.button("❌ Xác nhận xóa vĩnh viễn", key="btn_confirm_del_ns", type="primary", disabled=not has_delete_perm):
                if not has_delete_perm:
                    st.error("⚠️ Bạn không có quyền thực hiện hành động này.")
                else:
                    conn = database.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM nhan_su WHERE id = ?", (sel_id_del,))
                    conn.commit()
                    conn.close()
                    st.success("Đã xóa nhân viên thành công!")
                    st.rerun()
