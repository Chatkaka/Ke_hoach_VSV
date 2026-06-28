import os
import sys
import json
import io
import streamlit as st

# Safe import checks to prevent crashes if libraries are missing
GD_LIBS_AVAILABLE = False
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    GD_LIBS_AVAILABLE = True
except ImportError:
    pass

# Global sync status variables
_last_sync_status = "Chờ đồng bộ"
_last_sync_error = None

if not GD_LIBS_AVAILABLE:
    _last_sync_status = "Lỗi thư viện"
    _last_sync_error = "Thiếu thư viện google-api-python-client hoặc google-auth. Vui lòng cài đặt chúng."

def get_sync_status():
    return _last_sync_status, _last_sync_error

def set_sync_status(status, error=None):
    global _last_sync_status, _last_sync_error
    _last_sync_status = status
    _last_sync_error = error

def get_gdrive_service():
    if not GD_LIBS_AVAILABLE:
        set_sync_status("Lỗi thư viện", "Thiếu thư viện google-api-python-client hoặc google-auth.")
        return None
    
    info = None
    
    # 1. Try to load from local file gdrive_credentials.json
    local_creds_path = "gdrive_credentials.json"
    if os.path.exists(local_creds_path):
        try:
            with open(local_creds_path, "r", encoding="utf-8") as f:
                info = json.load(f)
        except Exception as e:
            set_sync_status("Lỗi cấu hình", f"Không thể đọc file gdrive_credentials.json: {e}")
            return None
            
    # 2. Try to load from Streamlit Secrets (check both upper and lowercase)
    if not info:
        gdrive_sa = st.secrets.get("GDRIVE_SERVICE_ACCOUNT") or st.secrets.get("gdrive_service_account")
        if gdrive_sa:
            try:
                # Handle both JSON string and pre-parsed TOML dict
                if isinstance(gdrive_sa, str):
                    info = json.loads(gdrive_sa)
                else:
                    info = dict(gdrive_sa)
            except Exception as e:
                set_sync_status("Lỗi cấu hình", f"Không thể phân giải Secrets credentials: {e}")
                return None

    if not info:
        return None

    try:
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/drive"]
        )
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        set_sync_status("Lỗi cấu hình", f"Lỗi khởi tạo credentials: {e}")
        return None

def upload_to_gdrive(local_path, gdrive_name):
    if not os.path.exists(local_path):
        return False
        
    service = get_gdrive_service()
    if not service:
        return False
        
    try:
        folder_id = st.secrets.get("GDRIVE_FOLDER_ID") or st.secrets.get("gdrive_folder_id")
        
        # Search if file already exists
        query = f"name = '{gdrive_name}' and trashed = false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
            
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get("files", [])
        
        media = MediaFileUpload(local_path, resumable=True)
        
        if files:
            # Update existing file
            file_id = files[0]["id"]
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            # Create new file
            file_metadata = {"name": gdrive_name}
            if folder_id:
                file_metadata["parents"] = [folder_id]
            service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            
        set_sync_status("Thành công")
        return True
    except Exception as e:
        set_sync_status("Thất bại", f"Lỗi upload {gdrive_name}: {e}")
        print(f"Failed to upload {gdrive_name} to Google Drive: {e}")
        return False

def download_from_gdrive(local_path, gdrive_name):
    service = get_gdrive_service()
    if not service:
        return False
        
    try:
        folder_id = st.secrets.get("GDRIVE_FOLDER_ID") or st.secrets.get("gdrive_folder_id")
        query = f"name = '{gdrive_name}' and trashed = false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
            
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get("files", [])
        
        if not files:
            return False
            
        file_id = files[0]["id"]
        request = service.files().get_media(fileId=file_id)
        
        # Write to local file
        with open(local_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                
        set_sync_status("Thành công")
        return True
    except Exception as e:
        set_sync_status("Thất bại", f"Lỗi download {gdrive_name}: {e}")
        print(f"Failed to download {gdrive_name} from Google Drive: {e}")
        return False
