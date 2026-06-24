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
    
    Hãy đối chiếu và chọn ra 'Mã BSC' phù hợp nhất từ danh sách các dự án sau đây:
    {json.dumps(clean_projects, ensure_ascii=False, indent=2)}
    
    Trả về kết quả dưới dạng JSON có cấu trúc như sau:
    {{
      "ma_bsc": "Mã BSC được chọn từ danh sách trên (ví dụ: VSV_QLTC_TT.01). Nếu không khớp bất kỳ mã nào, để trống hoặc null",
      "week_index": 1, // Số tuần (từ 1 đến 4, xác định từ báo cáo. Ví dụ: 'tuần này', 'tuần 1' -> 1)
      "week_kq": 0.22, // Kết quả thực tế của tuần dưới dạng số thực từ 0.0 đến 1.0 (ví dụ: 22% -> 0.22, chậm 3% so với kế hoạch -> nếu không ghi cụ thể kế hoạch, ước lượng hoặc chỉ lấy kết quả thực tế. Nếu không có để null)
      "week_danh_gia": "Đánh giá ngắn gọn nguyên nhân chậm hoặc tiến độ (ví dụ: 'Mưa lớn + nền yếu', nếu không có để null)",
      "bu_tien_do": {{
        "nguyen_nhan": "Nguyên nhân chậm tiến độ chi tiết (ví dụ: 'Mưa lớn kéo dài và nền đất bị yếu')",
        "giai_phap": "Giải pháp khắc phục/bù tiến độ (ví dụ: 'Tăng ca đêm')",
        "muc_cham_ngay": 5.0 // Số ngày chậm tiến độ dưới dạng số thực (nếu không đề cập, ước lượng hợp lý hoặc để 5.0)
      }} // Trả về đối tượng này nếu báo cáo đề cập đến việc chậm tiến độ và giải pháp bù, nếu không có thể để null
    }}
    
    Hãy đảm bảo đầu ra chỉ là JSON thô, không nằm trong khối markdown ```json ... ```.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
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
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    return response.text
