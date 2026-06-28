import sqlite3
import pandas as pd
import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.normpath(os.path.join(BASE_DIR, 'project_control.db'))
EXCEL_PATH = os.path.normpath(os.path.join(BASE_DIR, 'TDG_Masterfile BQLDA_v1_20260623.xlsx'))

def clean_date(val):
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (pd.Timestamp, datetime.datetime)):
        return val.strftime('%Y-%m-%d')
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ('none', 'nat', 'null'):
        return None
    # Try parsing different formats
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(val_str, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return val_str

def clean_float(val):
    if pd.isna(val) or val is None:
        return None
    try:
        return float(val)
    except ValueError:
        return None

def clean_str(val):
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    if not val_str or val_str.lower() == 'nan':
        return None
    return val_str

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def check_and_add_columns(cursor):
    # Dictionary of expected columns for tables to ensure self-healing schema migration
    expected_schemas = {
        "bu_tien_do": {
            "Ghi_chu": "TEXT"
        },
        "nhan_su": {
            "Ma_NV": "TEXT",
            "Ho_Ten": "TEXT",
            "Chuc_Vu": "TEXT",
            "Vai_Tro": "TEXT",
            "Email": "TEXT",
            "Xem": "INTEGER DEFAULT 1",
            "Them_HD": "INTEGER",
            "Sua": "INTEGER",
            "Xoa_HD": "INTEGER",
            "Sua_CDT_BD": "INTEGER",
            "Cap_Nhat_CDT": "INTEGER"
        },
        "audit_log": {
            "timestamp": "TEXT",
            "username": "TEXT",
            "action_type": "TEXT",
            "table_name": "TEXT",
            "record_id": "TEXT",
            "details": "TEXT"
        }
    }
    for table_name, cols in expected_schemas.items():
        # Check if table exists first
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            continue
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_cols = [row[1] for row in cursor.fetchall()]
        for col_name, col_type in cols.items():
            if col_name not in existing_cols:
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}")
                    print(f"Auto-migration: Added column '{col_name}' to table '{table_name}'")
                except Exception as e:
                    print(f"Error migrating column {col_name} in {table_name}: {e}")

def init_db(force_reseed=False):
    # Try downloading database from Google Drive on startup
    try:
        import gdrive_sync
        if gdrive_sync.download_from_gdrive(DB_PATH, "project_control.db"):
            print("Successfully downloaded latest database from Google Drive!")
            gdrive_sync.download_from_gdrive(EXCEL_PATH, "TDG_Masterfile BQLDA_v1_20260623.xlsx")
    except Exception as e:
        print(f"Google Drive startup download skipped/failed: {e}")

    db_exists = os.path.exists(DB_PATH)
    conn = get_connection()
    cursor = conn.cursor()

    # Create Master Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS master_bang_tonghop (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        TT TEXT,
        Ma_BSC TEXT,
        Goi_thau TEXT,
        Nhom_CT TEXT,
        Hang_muc TEXT,
        Phu_trach TEXT,
        Ngay_BD_YC TEXT,
        Ngay_KT_YC TEXT,
        Ngan_sach REAL,
        KH_phat_hanh_HSTKTC TEXT,
        TT_HSTKTC TEXT,
        TT_SPECS TEXT,
        TT_BOQ TEXT,
        KH_LCNT TEXT,
        TT_LCNT TEXT,
        KH_Ky_HDCU TEXT,
        TT_Ky_HDCU TEXT,
        KH_PD_KHCU TEXT,
        TT_KHCU TEXT,
        Gia_tri_HDCU REAL,
        KH_ky_PLHD TEXT,
        TT_Ky_PLHD TEXT,
        KH_PD_KHTK TEXT,
        TT_KHTK TEXT,
        Ngay_BD_Khoi_Cong TEXT,
        QA_KH_Thang REAL,
        QA_KQ_Thang REAL,
        QA_Danh_gia_Thang TEXT,
        KH_Thang REAL,
        KQ_Thang REAL,
        Danh_gia_Thang TEXT,
        T1_KH REAL,
        T1_KQ REAL,
        T1_Danh_gia TEXT,
        T2_KH REAL,
        T2_KQ REAL,
        T2_Danh_gia TEXT,
        T3_KH REAL,
        T3_KQ REAL,
        T3_Danh_gia TEXT,
        T4_KH REAL,
        T4_KQ REAL,
        T4_Danh_gia TEXT
    )
    """)

    # Create 01_HSo_TienKC
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hso_tienkc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Ma_BSC TEXT,
        Hang_muc TEXT,
        Loai_ho_so TEXT,
        Ten_san_pham TEXT,
        Link_luu_tru TEXT,
        Ngay_HT TEXT,
        Nguoi_lap TEXT,
        Nguoi_duyet TEXT,
        TT_duyet TEXT
    )
    """)

    # Create 02_KH_Thang_Tuan
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kh_thang_tuan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Ma_BSC TEXT,
        Hang_muc TEXT,
        Thang TEXT,
        Loai_tai_lieu TEXT,
        Noi_dung_chinh TEXT,
        Dat_YCKT_CDT TEXT,
        Link_tai_lieu TEXT,
        TT_lap TEXT,
        TT_duyet TEXT,
        Nguoi_lap TEXT,
        Nguoi_duyet TEXT,
        Ngay_duyet TEXT
    )
    """)

    # Create 03_Phat_sinh
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS phat_sinh (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Ma_PS TEXT,
        Ma_BSC TEXT,
        Hang_muc TEXT,
        Ngay_PS TEXT,
        Loai TEXT,
        Mo_ta TEXT,
        Nguyen_nhan TEXT,
        De_xuat_xu_ly TEXT,
        Gia_tri_phat_sinh REAL,
        Anh_huong_TD REAL,
        Link_ho_so TEXT,
        TT_Phe_duyet TEXT,
        Nguoi_duyet TEXT,
        Ngay_duyet TEXT,
        Noi_dung_dieu_chinh TEXT,
        Ghi_chu TEXT
    )
    """)

    # Create 04_CU_dac_thu
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cu_dac_thu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Ma_YC TEXT,
        Ma_BSC TEXT,
        Hang_muc TEXT,
        Ngay_YC TEXT,
        Loai_YC TEXT,
        Vat_tu_thiet_bi TEXT,
        Noi_dung_yeu_cau TEXT,
        KL REAL,
        DVT TEXT,
        Gia_tri_phat_sinh REAL,
        Trong_Ngoai_HDCU TEXT,
        Link_ho_so TEXT,
        TT_Phe_duyet TEXT,
        Nguoi_duyet TEXT,
        Ngay_can TEXT,
        TT_cung_ung TEXT,
        Ghi_chu TEXT
    )
    """)

    # Create 05_Bu_tien_do
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bu_tien_do (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Ma_BSC TEXT,
        Hang_muc TEXT,
        Ngay_phat_hien TEXT,
        Muc_cham_ngay REAL,
        Nguyen_nhan TEXT,
        Phuong_an TEXT,
        Chi_tiet_giai_phap TEXT,
        Moc_cam_ket_HT TEXT,
        Link_phuong_an TEXT,
        TT_duyet TEXT,
        Nguoi_duyet TEXT,
        KQ_thuc_hien_bu TEXT,
        TT_Trien_khai TEXT,
        Ghi_chu TEXT
    )
    """)

    # Create sys_config Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sys_config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    # Create audit_log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        username TEXT,
        action_type TEXT,
        table_name TEXT,
        record_id TEXT,
        details TEXT
    )
    """)

    # Create nhan_su Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS nhan_su (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Ma_NV TEXT,
        Ho_Ten TEXT,
        Chuc_Vu TEXT,
        Vai_Tro TEXT,
        Email TEXT,
        Xem INTEGER DEFAULT 1,
        Them_HD INTEGER,
        Sua INTEGER,
        Xoa_HD INTEGER,
        Sua_CDT_BD INTEGER,
        Cap_Nhat_CDT INTEGER
    )
    """)

    # Run Schema Self-Healing to add any missing columns in existing DB files
    check_and_add_columns(cursor)

    # Check if database has been seeded using sys_config table
    cursor.execute("SELECT value FROM sys_config WHERE key='is_seeded'")
    seeded_row = cursor.fetchone()
    already_seeded = seeded_row is not None and seeded_row[0] == '1'

    # Seed personnel if forced reseed, or database is brand new and not seeded
    if force_reseed or not already_seeded:
        cursor.execute("SELECT COUNT(*) FROM nhan_su")
        count_ns = cursor.fetchone()[0]
        if count_ns == 0:
            personnel_data = [
                ("80", "Cao Thị An", "Phó phòng", "Trống", "caothian11@gmail.com", 1, 0, 1, 0, 0, 0),
                ("58", "Hoàng Văn Vượng", "CV QLCL", "User2", "hoangvuongdhv@gmail.com", 1, 0, 1, 0, 0, 0),
                ("38", "Hồ Nghĩa Chất", "Admin", "admin2", "Hochat.tayan@gmail.com", 1, 1, 1, 1, 1, 1),
                ("467", "Lê Thị Ngọc Hoa", "NV hỗ trợ", "Trống", "lengochoa289@gmail.com", 1, 0, 0, 0, 0, 0),
                ("364", "Lê Xuân Văn", "CV QLCL", "User2", "lexuanvankt@gmail.com", 1, 0, 1, 0, 0, 0),
                ("76", "Nguyễn Hoàng Kiên", "CV Vật tư", "Trống", "kienprotl4@gmail.com", 1, 0, 0, 0, 0, 0),
                ("312", "Nguyễn Thành Chung", "CV QLCL", "User2", "thanhchunglcc@gmail.com", 1, 0, 1, 0, 0, 0)
            ]
            cursor.executemany("""
                INSERT INTO nhan_su (Ma_NV, Ho_Ten, Chuc_Vu, Vai_Tro, Email, Xem, Them_HD, Sua, Xoa_HD, Sua_CDT_BD, Cap_Nhat_CDT)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, personnel_data)
        
        # Write seeded flag to prevent any future re-seeding
        cursor.execute("INSERT OR REPLACE INTO sys_config (key, value) VALUES ('is_seeded', '1')")

    conn.commit()

    # Only seed from Excel if master table is empty or forced reseed
    cursor.execute("SELECT COUNT(*) FROM master_bang_tonghop")
    count_master = cursor.fetchone()[0]
    if force_reseed or count_master == 0:
        if os.path.exists(EXCEL_PATH):
            print("Seeding database from Excel file...")
            seed_from_excel(conn)
        else:
            print("Excel file not found. Seeding skipped.")

    conn.close()

def seed_from_excel(conn, excel_file=None):
    if excel_file is None:
        excel_file = EXCEL_PATH
    cursor = conn.cursor()

    # Clear existing data to avoid duplicates on forced reseed
    cursor.execute("DELETE FROM master_bang_tonghop")
    cursor.execute("DELETE FROM hso_tienkc")
    cursor.execute("DELETE FROM kh_thang_tuan")
    cursor.execute("DELETE FROM phat_sinh")
    cursor.execute("DELETE FROM cu_dac_thu")
    cursor.execute("DELETE FROM bu_tien_do")

    # 1. Seed MASTER_BANG_TONGHOP
    df_master = pd.read_excel(excel_file, sheet_name='BANG TONG HOP', header=None)
    # The actual data starts from Row 6 (index 5)
    current_pl = None
    for idx in range(5, len(df_master)):
        row = df_master.iloc[idx].values
        # Break if row is empty
        if len(row) < 5 or (pd.isna(row[0]) and pd.isna(row[4])):
            continue

        tt = clean_str(row[0])
        ma_bsc = clean_str(row[1])
        goi_thau = clean_str(row[2])
        
        # Track current PL package
        if goi_thau and goi_thau.upper().startswith('PL'):
            current_pl = goi_thau
            
        # Inherit current PL if row Goi_thau doesn't start with PL (or is empty)
        if not goi_thau or not goi_thau.upper().startswith('PL'):
            if current_pl:
                goi_thau = current_pl
            else:
                continue
        nhom_ct = clean_str(row[3])
        hang_muc = clean_str(row[4])
        phu_trach = clean_str(row[5])
        ngay_bd_yc = clean_date(row[6])
        ngay_kt_yc = clean_date(row[7])
        ngan_sach = clean_float(row[8])
        kh_phat_hanh_hstktc = clean_date(row[9])
        tt_hstktc = clean_str(row[10])
        tt_specs = clean_str(row[11])
        tt_boq = clean_str(row[12])
        kh_lcnt = clean_date(row[13])
        tt_lcnt = clean_str(row[14])
        kh_ky_hdcu = clean_date(row[15])
        tt_ky_hdcu = clean_str(row[16])
        kh_pd_khcu = clean_date(row[17])
        tt_khcu = clean_str(row[18])
        gia_tri_hdcu = clean_float(row[19])
        # Column 20 is % HĐCU/NS
        kh_ky_plhd = clean_date(row[21])
        tt_ky_plhd = clean_str(row[22])
        kh_pd_khtk = clean_date(row[23])
        tt_khtk = clean_str(row[24])
        # Column 25, 26, 27, 28 are DK1, DK2, DK3, Dieu kien du
        ngay_bd_khoi_cong = clean_date(row[29])
        # Column 30-33 are computed
        # Column 34-37 are computed
        qa_kh_thang = clean_float(row[38])
        qa_kq_thang = clean_float(row[39])
        qa_danh_gia_thang = clean_str(row[40])
        kh_thang = clean_float(row[41])
        kq_thang = clean_float(row[42])
        danh_gia_thang = clean_str(row[43])
        t1_kh = clean_float(row[44])
        t1_kq = clean_float(row[45])
        t1_danh_gia = clean_str(row[46])
        t2_kh = clean_float(row[47])
        t2_kq = clean_float(row[48])
        t2_danh_gia = clean_str(row[49])
        t3_kh = clean_float(row[50])
        t3_kq = clean_float(row[51])
        t3_danh_gia = clean_str(row[52])
        t4_kh = clean_float(row[53])
        t4_kq = clean_float(row[54])
        t4_danh_gia = clean_str(row[55])

        cursor.execute("""
        INSERT INTO master_bang_tonghop (
            TT, Ma_BSC, Goi_thau, Nhom_CT, Hang_muc, Phu_trach, Ngay_BD_YC, Ngay_KT_YC, Ngan_sach,
            KH_phat_hanh_HSTKTC, TT_HSTKTC, TT_SPECS, TT_BOQ, KH_LCNT, TT_LCNT, KH_Ky_HDCU, TT_Ky_HDCU,
            KH_PD_KHCU, TT_KHCU, Gia_tri_HDCU, KH_ky_PLHD, TT_Ky_PLHD, KH_PD_KHTK, TT_KHTK, Ngay_BD_Khoi_Cong,
            QA_KH_Thang, QA_KQ_Thang, QA_Danh_gia_Thang, KH_Thang, KQ_Thang, Danh_gia_Thang,
            T1_KH, T1_KQ, T1_Danh_gia, T2_KH, T2_KQ, T2_Danh_gia, T3_KH, T3_KQ, T3_Danh_gia, T4_KH, T4_KQ, T4_Danh_gia
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tt, ma_bsc, goi_thau, nhom_ct, hang_muc, phu_trach, ngay_bd_yc, ngay_kt_yc, ngan_sach,
            kh_phat_hanh_hstktc, tt_hstktc, tt_specs, tt_boq, kh_lcnt, tt_lcnt, kh_ky_hdcu, tt_ky_hdcu,
            kh_pd_khcu, tt_khcu, gia_tri_hdcu, kh_ky_plhd, tt_ky_plhd, kh_pd_khtk, tt_khtk, ngay_bd_khoi_cong,
            qa_kh_thang, qa_kq_thang, qa_danh_gia_thang, kh_thang, kq_thang, danh_gia_thang,
            t1_kh, t1_kq, t1_danh_gia, t2_kh, t2_kq, t2_danh_gia, t3_kh, t3_kq, t3_danh_gia, t4_kh, t4_kq, t4_danh_gia
        ))

    # 2. Seed 01_HSo TienKC
    df_01 = pd.read_excel(excel_file, sheet_name='01_HSo TienKC', header=None)
    for idx in range(2, len(df_01)):
        row = df_01.iloc[idx].values
        if len(row) < 10 or pd.isna(row[1]):
            continue
        cursor.execute("""
        INSERT INTO hso_tienkc (Ma_BSC, Hang_muc, Loai_ho_so, Ten_san_pham, Link_luu_tru, Ngay_HT, Nguoi_lap, Nguoi_duyet, TT_duyet)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (clean_str(row[1]), clean_str(row[2]), clean_str(row[3]), clean_str(row[4]), clean_str(row[5]), clean_date(row[6]), clean_str(row[7]), clean_str(row[8]), clean_str(row[9])))

    # 3. Seed 02_KH Thang_Tuan
    df_02 = pd.read_excel(excel_file, sheet_name='02_KH Thang_Tuan', header=None)
    for idx in range(2, len(df_02)):
        row = df_02.iloc[idx].values
        if len(row) < 13 or pd.isna(row[1]):
            continue
        cursor.execute("""
        INSERT INTO kh_thang_tuan (Ma_BSC, Hang_muc, Thang, Loai_tai_lieu, Noi_dung_chinh, Dat_YCKT_CDT, Link_tai_lieu, TT_lap, TT_duyet, Nguoi_lap, Nguoi_duyet, Ngay_duyet)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (clean_str(row[1]), clean_str(row[2]), clean_str(row[3]), clean_str(row[4]), clean_str(row[5]), clean_str(row[6]), clean_str(row[7]), clean_str(row[8]), clean_str(row[9]), clean_str(row[10]), clean_str(row[11]), clean_date(row[12])))

    # 4. Seed 03_Phat sinh
    df_03 = pd.read_excel(excel_file, sheet_name='03_Phat sinh', header=None)
    for idx in range(2, len(df_03)):
        row = df_03.iloc[idx].values
        if len(row) < 15 or pd.isna(row[2]):
            continue
        cursor.execute("""
        INSERT INTO phat_sinh (Ma_PS, Ma_BSC, Hang_muc, Ngay_PS, Loai, Mo_ta, Nguyen_nhan, De_xuat_xu_ly, Gia_tri_phat_sinh, Anh_huong_TD, Link_ho_so, TT_Phe_duyet, Nguoi_duyet, Ngay_duyet, Noi_dung_dieu_chinh, Ghi_chu)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (clean_str(row[1]), clean_str(row[2]), clean_str(row[3]), clean_date(row[4]), clean_str(row[5]), clean_str(row[6]), clean_str(row[7]), clean_str(row[8]), clean_float(row[9]), clean_float(row[10]), clean_str(row[11]), clean_str(row[12]), clean_str(row[13]), clean_date(row[14]), clean_str(row[15]) if len(row)>15 else None, clean_str(row[16]) if len(row)>16 else None))

    # 5. Seed 04_CU dac thu
    df_04 = pd.read_excel(excel_file, sheet_name='04_CU dac thu', header=None)
    for idx in range(2, len(df_04)):
        row = df_04.iloc[idx].values
        if len(row) < 15 or pd.isna(row[2]):
            continue
        cursor.execute("""
        INSERT INTO cu_dac_thu (Ma_YC, Ma_BSC, Hang_muc, Ngay_YC, Loai_YC, Vat_tu_thiet_bi, Noi_dung_yeu_cau, KL, DVT, Gia_tri_phat_sinh, Trong_Ngoai_HDCU, Link_ho_so, TT_Phe_duyet, Nguoi_duyet, Ngay_can, TT_cung_ung, Ghi_chu)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (clean_str(row[1]), clean_str(row[2]), clean_str(row[3]), clean_date(row[4]), clean_str(row[5]), clean_str(row[6]), clean_str(row[7]), clean_float(row[8]), clean_str(row[9]), clean_float(row[10]), clean_str(row[11]), clean_str(row[12]), clean_str(row[13]), clean_str(row[14]), clean_date(row[15]) if len(row)>15 else None, clean_str(row[16]) if len(row)>16 else None, clean_str(row[17]) if len(row)>17 else None))

    # 6. Seed 05_Bu tien do
    df_05 = pd.read_excel(excel_file, sheet_name='05_Bu tien do', header=None)
    for idx in range(2, len(df_05)):
        row = df_05.iloc[idx].values
        if len(row) < 14 or pd.isna(row[1]):
            continue
        cursor.execute("""
        INSERT INTO bu_tien_do (Ma_BSC, Hang_muc, Ngay_phat_hien, Muc_cham_ngay, Nguyen_nhan, Phuong_an, Chi_tiet_giai_phap, Moc_cam_ket_HT, Link_phuong_an, TT_duyet, Nguoi_duyet, KQ_thuc_hien_bu, TT_Trien_khai, Ghi_chu)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (clean_str(row[1]), clean_str(row[2]), clean_date(row[3]), clean_float(row[4]), clean_str(row[5]), clean_str(row[6]), clean_str(row[7]), clean_date(row[8]), clean_str(row[9]), clean_str(row[10]), clean_str(row[11]), clean_str(row[12]), clean_str(row[13]), clean_str(row[14]) if len(row)>14 else None))

    conn.commit()
    print("Database seeding completed successfully.")

if __name__ == '__main__':
    init_db(force_reseed=True)


def log_action(username, action_type, table_name, record_id, details):
    try:
        import datetime
        conn = get_connection()
        cursor = conn.cursor()
        now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO audit_log (timestamp, username, action_type, table_name, record_id, details)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (now_str, username, action_type, table_name, str(record_id), details))
        conn.commit()
        conn.close()
        
        # Trigger background GDrive upload after logging an action
        try:
            import gdrive_sync
            import threading
            threading.Thread(target=gdrive_sync.upload_to_gdrive, args=(DB_PATH, "project_control.db"), daemon=True).start()
        except Exception:
            pass
    except Exception as e:
        print(f"Error writing audit log: {e}")
