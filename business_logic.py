import datetime
from database import get_connection

def get_current_date():
    # According to prompt metadata, the system current date is June 24, 2026
    return datetime.date(2026, 6, 24)

def calculate_project_metrics(project, conn=None):
    """
    Computes all calculated fields for a project row from database.
    If conn is provided, uses it, otherwise opens a new one.
    """
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    cursor = conn.cursor()
    ma_bsc = project['Ma_BSC']

    # For sub-items (WBS) with blank Ma_BSC, we skip calculations or return empty/default values
    if not ma_bsc:
        if should_close:
            conn.close()
        return {
            'DK1_HSKT': None,
            'DK2_HDCU': None,
            'DK3_KHTK': None,
            'Dieu_kien_du': None,
            'Approved_HSo_Count': 0,
            'Luy_ke_HDCU': project['Gia_tri_HDCU'] or 0.0,
            'Luy_ke_Phat_sinh': 0.0,
            'Total_Cost': project['Gia_tri_HDCU'] or 0.0,
            'Pending_PS_Count': 0,
            'Pending_CU_Count': 0,
            'Running_Bu_Count': 0,
            'Co_Canh_bao': 'GREEN',
            'Canh_bao_Text': 'Bình thường',
            'Percent_HDCU_NS': (project['Gia_tri_HDCU'] / project['Ngan_sach']) if (project['Gia_tri_HDCU'] and project['Ngan_sach']) else None,
            'KH_Thang_Tuan_Ratio': '0/0'
        }

    # 1. Count of Approved records in 01_HSo_TienKC
    cursor.execute("""
        SELECT COUNT(*) FROM hso_tienkc 
        WHERE Ma_BSC = ? AND (TT_duyet = 'Đã duyệt' OR TT_duyet = 'Approved')
    """, (ma_bsc,))
    approved_hso_count = cursor.fetchone()[0]

    # 2. Sum of Approved values in 03_Phat_sinh
    cursor.execute("""
        SELECT SUM(Gia_tri_phat_sinh) FROM phat_sinh 
        WHERE Ma_BSC = ? AND (TT_Phe_duyet = 'Đã duyệt' OR TT_Phe_duyet = 'Approved')
    """, (ma_bsc,))
    res_ps = cursor.fetchone()[0]
    approved_ps_sum = float(res_ps) if res_ps is not None else 0.0

    # 3. Counts of Pending changes (03_Phat_sinh & 04_CU_dac_thu) and Active Catch-up (05_Bu_tien_do)
    cursor.execute("""
        SELECT COUNT(*) FROM phat_sinh 
        WHERE Ma_BSC = ? AND (TT_Phe_duyet = 'Chờ duyệt' OR TT_Phe_duyet = 'Pending')
    """, (ma_bsc,))
    pending_ps_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM cu_dac_thu 
        WHERE Ma_BSC = ? AND (TT_Phe_duyet = 'Chờ duyệt' OR TT_Phe_duyet = 'Pending')
    """, (ma_bsc,))
    pending_cu_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM bu_tien_do 
        WHERE Ma_BSC = ? AND (TT_Trien_khai = 'Đang thực hiện' OR TT_Trien_khai = 'Running')
    """, (ma_bsc,))
    running_bu_count = cursor.fetchone()[0]

    # 4. Count of monthly plans in 02_KH_Thang_Tuan (approved / total)
    cursor.execute("SELECT COUNT(*) FROM kh_thang_tuan WHERE Ma_BSC = ?", (ma_bsc,))
    total_kh_tuan = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM kh_thang_tuan 
        WHERE Ma_BSC = ? AND (TT_duyet = 'Đã duyệt' OR TT_duyet = 'Approved')
    """, (ma_bsc,))
    approved_kh_tuan = cursor.fetchone()[0]
    kh_thang_tuan_ratio = f"{approved_kh_tuan}/{total_kh_tuan}"

    if should_close:
        conn.close()

    # --- Calculations ---
    # DK1_HSKT = True if TT_HSTKTC in ('Hoàn thiện', 'Đã phát hành') and TT_BOQ == 'Đã bàn giao'
    tt_hstktc = project['TT_HSTKTC'] or ''
    tt_boq = project['TT_BOQ'] or ''
    dk1 = (tt_hstktc in ('Hoàn thiện', 'Đã phát hành')) and (tt_boq == 'Đã bàn giao')

    # DK2_HDCU = True if TT_Ky_HDCU == 'Đã CU'
    tt_ky_hdcu = project['TT_Ky_HDCU'] or ''
    dk2 = (tt_ky_hdcu == 'Đã CU')

    # DK3_KHTK = True if TT_KHTK == 'Đã duyệt'
    tt_khtk = project['TT_KHTK'] or ''
    dk3 = (tt_khtk == 'Đã duyệt')

    # Dieu_kien_du = 'ĐỦ ĐK KHỞI CÔNG' if dk1 and dk2 and dk3 else 'THIẾU ĐK'
    dieu_kien_du = 'ĐỦ ĐK KHỞI CÔNG' if (dk1 and dk2 and dk3) else 'THIẾU ĐK'

    # Financials
    ngan_sach = project['Ngan_sach'] or 0.0
    gia_tri_hdcu = project['Gia_tri_HDCU'] or 0.0
    percent_hdcu_ns = (gia_tri_hdcu / ngan_sach) if ngan_sach > 0 else 0.0
    total_cost = gia_tri_hdcu + approved_ps_sum

    # Date check
    current_date = get_current_date()
    ngay_bd_khoi_cong_str = project['Ngay_BD_Khoi_Cong']
    ngay_bd_khoi_cong = None
    if ngay_bd_khoi_cong_str:
        try:
            ngay_bd_khoi_cong = datetime.datetime.strptime(ngay_bd_khoi_cong_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    # Warning logic
    # RED: (Dieu_kien_du == 'THIẾU ĐK' and current_date >= Ngay_BD_Khoi_Cong) OR (Total Costs > Ngan_sach)
    is_red = False
    red_reasons = []
    if (dieu_kien_du == 'THIẾU ĐK' and ngay_bd_khoi_cong and current_date >= ngay_bd_khoi_cong):
        is_red = True
        red_reasons.append("Thiếu điều kiện khởi công nhưng đã quá ngày khởi công")
    if (ngan_sach > 0 and total_cost > ngan_sach):
        is_red = True
        red_reasons.append(f"Vượt ngân sách: Chi phí ({total_cost:.2f} tỷ) > Ngân sách ({ngan_sach:.2f} tỷ)")

    # ORANGE: Any Pending in 03, 04 OR Any Running in 05 OR (KQ_Thang < KH_Thang)
    is_orange = False
    orange_reasons = []
    if pending_ps_count > 0:
        is_orange = True
        orange_reasons.append(f"Có {pending_ps_count} hồ sơ phát sinh đang chờ duyệt")
    if pending_cu_count > 0:
        is_orange = True
        orange_reasons.append(f"Có {pending_cu_count} yêu cầu cung ứng đặc thù đang chờ duyệt")
    if running_bu_count > 0:
        is_orange = True
        orange_reasons.append(f"Có {running_bu_count} phương án bù tiến độ đang triển khai")
    
    kh_thang = project['KH_Thang'] or 0.0
    kq_thang = project['KQ_Thang'] or 0.0
    if kq_thang < kh_thang:
        is_orange = True
        orange_reasons.append(f"Kết quả thực hiện tháng ({kq_thang*100:.1f}%) chậm hơn kế hoạch ({kh_thang*100:.1f}%)")

    # YELLOW: count of Approved records in 01 < 8
    is_yellow = False
    yellow_reasons = []
    if approved_hso_count < 8:
        is_yellow = True
        yellow_reasons.append(f"Số lượng hồ sơ tiền khởi công đã duyệt ({approved_hso_count}/8) chưa đủ")

    # Resolve Warning Color
    warning_status = 'GREEN'
    warning_text = 'Bình thường'
    if is_red:
        warning_status = 'RED'
        warning_text = " | ".join(red_reasons)
    elif is_orange:
        warning_status = 'ORANGE'
        warning_text = " | ".join(orange_reasons)
    elif is_yellow:
        warning_status = 'YELLOW'
        warning_text = " | ".join(yellow_reasons)

    return {
        'DK1_HSKT': dk1,
        'DK2_HDCU': dk2,
        'DK3_KHTK': dk3,
        'Dieu_kien_du': dieu_kien_du,
        'Approved_HSo_Count': approved_hso_count,
        'Luy_ke_HDCU': gia_tri_hdcu,
        'Luy_ke_Phat_sinh': approved_ps_sum,
        'Total_Cost': total_cost,
        'Pending_PS_Count': pending_ps_count,
        'Pending_CU_Count': pending_cu_count,
        'Running_Bu_Count': running_bu_count,
        'Co_Canh_bao': warning_status,
        'Canh_bao_Text': warning_text,
        'Percent_HDCU_NS': percent_hdcu_ns,
        'KH_Thang_Tuan_Ratio': kh_thang_tuan_ratio
    }

def get_all_projects_calculated():
    """
    Returns all projects from SQLite database with calculated fields added.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM master_bang_tonghop ORDER BY id ASC")
    projects = [dict(row) for row in cursor.fetchall()]
    
    calculated_projects = []
    for p in projects:
        metrics = calculate_project_metrics(p, conn)
        p.update(metrics)
        calculated_projects.append(p)
        
    conn.close()
    return calculated_projects

def get_project_by_id(project_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM master_bang_tonghop WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        project = dict(row)
        metrics = calculate_project_metrics(project)
        project.update(metrics)
        return project
    return None
