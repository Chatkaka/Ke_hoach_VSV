import os
import json
from google import genai
from google.genai import types

def get_client(api_key=None):
    # Check provided key first, then look for environment variable
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("Thiếu API Key. Vui lòng nhập API Key trong thanh bên (sidebar) để sử dụng các tính năng AI.")
    return genai.Client(api_key=key)

def parse_raw_report(raw_text, projects_list, api_key=None):
    """
    Calls Gemini to parse a raw text report and match it to a project.
    """
    client = get_client(api_key)
    
    # Filter projects list to make it small and clear for the prompt
    clean_projects = [
        {"Ma_BSC": p.get("Ma_BSC"), "Hang_muc": p.get("Hang_muc")} 
        for p in projects_list if p.get("Ma_BSC")
    ]
    
    prompt = f"""
    Bạn là một trợ lý AI chuyên nghiệp phân tích báo cáo dự án xây dựng tại Việt Nam.
    Hãy phân tích báo cáo thô sau đây:
    "{raw_text}"
    
    Hãy đối chiếu báo cáo thô để tìm ra các hành động (actions) cập nhật hoặc chèn dữ liệu tương ứng cho các dự án sau đây. 
    Các dự án hiện có trong hệ thống (chỉ chọn từ danh sách này):
    {json.dumps(clean_projects, ensure_ascii=False, indent=2)}
    
    Hãy trả về kết quả dưới dạng JSON có cấu trúc như sau:
    {{
      "actions": [
        // 1. Cập nhật tiến độ tuần cho Bảng Master chính (nếu báo cáo đề cập tiến độ tuần, ví dụ: 'tuần 1', 'tuần này đạt 20%'):
        {{
          "type": "update_master_progress",
          "ma_bsc": "Mã BSC phù hợp nhất được đối chiếu từ danh sách trên",
          "week_index": 1, // Tuần cập nhật (số nguyên từ 1 đến 4)
          "week_kq": 0.2, // Kết quả thực tế tuần dưới dạng số thực từ 0.0 đến 1.0 (ví dụ: 20% -> 0.2)
          "week_danh_gia": "Đánh giá tiến độ ngắn gọn hoặc nguyên nhân chậm (ví dụ: 'Chậm do mưa bão')"
        }},
        // 2. Thêm hồ sơ đầu vào (nếu đề cập hoàn thành/duyệt hồ sơ pháp lý, specs, BOQ, thiết kế...):
        {{
          "type": "insert_hso_tienkc",
          "ma_bsc": "Mã BSC phù hợp",
          "loai_ho_so": "Loại hồ sơ (phải là một trong: HSTKTC, SPECS, BOQ/KL, KQ LCNT, HĐCU, PD KHCU, Ký PLHĐ, PD KHTK)",
          "ten_san_pham": "Tên văn bản / Số hiệu tài liệu được ký",
          "link_luu_tru": "LINK lưu trữ (nếu có, nếu không để null)",
          "nguoi_lap": "Kỹ sư lập",
          "nguoi_duyet": "Kỹ sư duyệt",
          "tt_duyet": "Trạng thái duyệt (Chưa lập, Đang lập, Chờ duyệt, Đã duyệt, Từ chối)"
        }},
        // 3. Thêm kế hoạch tháng/tuần (nếu đề cập trình duyệt kế hoạch thi công, biện pháp thi công, biểu đồ nhân lực...):
        {{
          "type": "insert_kh_thang_tuan",
          "ma_bsc": "Mã BSC phù hợp",
          "thang": "Tháng kiểm soát (Ví dụ: 06/2026)",
          "loai_tai_lieu": "Loại tài liệu (phải là một trong: Biện pháp thi công, Kế hoạch cung ứng, Biểu đồ nhân lực, Biểu đồ máy móc thiết bị, Biểu đồ cung ứng)",
          "noi_dung_chinh": "Nội dung kế hoạch / đệ trình chính",
          "dat_yckt_cdt": "Đạt yêu cầu kỹ thuật CĐT? (Có, Chưa, Đang sửa đổi)",
          "link_tai_lieu": "LINK tài liệu",
          "tt_lap": "Trạng thái lập (Chưa lập, Đang lập, Đã lập)",
          "tt_duyet": "Trạng thái duyệt (Chưa lập, Đang lập, Chờ duyệt, Đã duyệt, Từ chối)",
          "nguoi_lap": "Nhà thầu lập",
          "nguoi_duyet": "Cán bộ duyệt"
        }},
        // 4. Báo cáo phát sinh chi phí/khối lượng/thiết kế ngoài kế hoạch (nếu có phát sinh):
        {{
          "type": "insert_phat_sinh",
          "ma_ps": "Mã Phát sinh (ví dụ: PS.CT01.03, tự đặt mã hợp lý nếu không có)",
          "ma_bsc": "Mã BSC phù hợp",
          "loai": "Phân loại phát sinh (Phát sinh khối lượng, Sai khác thiết kế, Biện pháp thi công phát sinh, Khác)",
          "mo_ta": "Mô tả chi tiết hạng mục phát sinh",
          "nguyen_nhan": "Nguyên nhân phát sinh",
          "de_xuat_xu_ly": "Đề xuất hướng xử lý",
          "gia_tri_phat_sinh": 0.5, // Giá trị phát sinh (tỷ đồng, số thực)
          "anh_huong_td": 3, // Số ngày chậm tiến độ dự kiến (số nguyên)
          "link_ho_so": "LINK hồ sơ phát sinh",
          "tt_phe_duyet": "Trạng thái duyệt (Chờ duyệt, Đã duyệt, Nháp)",
          "nguoi_duyet": "Cán bộ thẩm định"
        }},
        // 5. Yêu cầu cung ứng vật tư đột xuất / đặc thù (nếu đề cập yêu cầu mua sắm đặc thù, thay thế vật liệu...):
        {{
          "type": "insert_cu_dac_thu",
          "ma_yc": "Mã yêu cầu (ví dụ: YC.CT01.03, tự đặt hợp lý nếu không có)",
          "ma_bsc": "Mã BSC phù hợp",
          "loai_yc": "Tính chất đệ trình (Đặc thù, Đột xuất, Thay thế vật liệu)",
          "vat_tu_thiet_bi": "Tên vật tư / Thiết bị cần mua",
          "noi_dung_yeu_cau": "Đặc tả yêu cầu và lý do",
          "kl": 5.0, // Khối lượng (số thực)
          "dvt": "Đơn vị tính (ĐVT, ví dụ: Tấn, m3, Cái...)",
          "gia_tri_phat_sinh": 0.1, // Giá trị dự toán (tỷ đồng, số thực)
          "trong_ngoai_hdcu": "Trong/Ngoài phạm vi HĐCU (Trong HĐCU, Ngoài HĐCU)",
          "link_ho_so": "LINK tài liệu kỹ thuật",
          "tt_phe_duyet": "Trạng thái duyệt (Chờ duyệt, Đã duyệt)",
          "nguoi_duyet": "Người duyệt"
        }},
        // 6. Phương án bù tiến độ (nếu báo cáo nói chậm tiến độ và có biện pháp khắc phục bù tiến độ):
        {{
          "type": "insert_bu_tien_do",
          "ma_bsc": "Mã BSC phù hợp",
          "muc_cham_ngay": 5.0, // Số ngày bị trễ (số thực)
          "nguyen_nhan": "Nguyên nhân chậm trễ",
          "phuong_an": "Tên giải pháp bù nhanh chính",
          "chi_tiet_giai_phap": "Kế hoạch triển khai chi tiết bù",
          "moc_cam_ket_ht": "YYYY-MM-DD", // Hạn cuối cam kết bù xong (định dạng ngày YYYY-MM-DD)
          "link_phuong_an": "LINK phương án bù",
          "tt_duyet": "Tình trạng duyệt (Chờ duyệt, Đã duyệt)",
          "nguoi_duyet": "Cán bộ duyệt",
          "kq_thuc_hien_bu": "Đánh giá kết quả bù",
          "tt_trien_khai": "Trạng thái triển khai (Đang thực hiện, Đã hoàn thành, Đóng)"
        }}
      ]
    }}
    
    Hãy đảm bảo đầu ra chỉ là JSON thô, không nằm trong khối markdown ```json ... ```.
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    try:
        data = json.loads(response.text)
        return data
    except Exception as e:
        raise ValueError(f"Không thể phân tích phản hồi từ Gemini thành JSON. Phản hồi thô: {response.text}") from e

def get_risk_advisor_solutions(project_data, api_key=None):
    """
    Calls Gemini to generate construction mitigation solutions based on project parameters.
    """
    client = get_client(api_key)
    
    prompt = f"""
    Bạn là chuyên gia tư vấn quản lý dự án và kỹ thuật thi công xây dựng cao cấp.
    Hãy phân tích thông tin chi tiết của dự án đang bị cảnh báo sau đây:
    - Mã BSC: {project_data.get('Ma_BSC')}
    - Gói thầu: {project_data.get('Goi_thau')}
    - Nhóm công trình: {project_data.get('Nhom_CT')}
    - Hạng mục: {project_data.get('Hang_muc')}
    - Phụ trách: {project_data.get('Phu_trach')}
    - Ngân sách: {project_data.get('Ngan_sach')} tỷ
    - Giá trị hợp đồng cung ứng: {project_data.get('Gia_tri_HDCU')} tỷ
    - Lũy kế tổng chi phí thực tế: {project_data.get('Total_Cost')} tỷ
    - Điều kiện khởi công: {project_data.get('Dieu_kien_du')} (DK1 HSKT: {project_data.get('DK1_HSKT')}, DK2 HĐCU: {project_data.get('DK2_HDCU')}, DK3 KHTK: {project_data.get('DK3_KHTK')})
    - Ngày bắt đầu khởi công theo kế hoạch: {project_data.get('Ngay_BD_Khoi_Cong')}
    - Tình trạng cảnh báo hiện tại: {project_data.get('Co_Canh_bao')}
    - Lý do cảnh báo chi tiết: {project_data.get('Canh_bao_Text')}
    - Kế hoạch tháng: {project_data.get('KH_Thang', 0)*100 if project_data.get('KH_Thang') else 0}%
    - Kết quả thực tế tháng: {project_data.get('KQ_Thang', 0)*100 if project_data.get('KQ_Thang') else 0}%
    - Đánh giá hiện trạng: {project_data.get('Danh_gia_Thang')}
    
    Dựa trên dữ liệu trên, hãy đưa ra một kế hoạch hành động khắc phục cụ thể, thiết thực và có thể triển khai ngay (actionable solutions). Hãy tập trung vào:
    1. Các phương án rút ngắn tiến độ (chỉ rõ phương pháp Crashing - tăng lực lượng/tăng ca, hoặc Fast-tracking - song song hóa công việc) phù hợp với nguyên nhân chậm.
    2. Giải pháp tháo gỡ nút thắt về hồ sơ (nếu thiếu điều kiện khởi công) hoặc điều chỉnh ngân sách, vật tư đặc thù.
    3. Đề xuất quy trình kiểm soát chất lượng QA/QC để tránh rủi ro phát sinh lại.
    
    Hãy viết bằng tiếng Việt, trình bày dưới dạng Markdown chuyên nghiệp, súc tích và mạch lạc với các gạch đầu dòng rõ ràng.
    """
    
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt
    )
    
    return response.text
