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

def get_gdrive_service():
    if not GD_LIBS_AVAILABLE:
        return None
    
    # Try to load from Streamlit Secrets
    gdrive_sa = st.secrets.get("GDRIVE_SERVICE_ACCOUNT", None)
    if gdrive_sa:
        try:
            # Parse service account JSON from secret string
            info = json.loads(gdrive_sa)
            creds = service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/drive"]
            )
            return build("drive", "v3", credentials=creds)
        except Exception as e:
            print(f"Error initializing Google Drive API: {e}")
            return None
    return None

def upload_to_gdrive(local_path, gdrive_name):
    if not os.path.exists(local_path):
        return False
        
    service = get_gdrive_service()
    if not service:
        return False
        
    try:
        folder_id = st.secrets.get("GDRIVE_FOLDER_ID", None)
        
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
        return True
    except Exception as e:
        print(f"Failed to upload {gdrive_name} to Google Drive: {e}")
        return False

def download_from_gdrive(local_path, gdrive_name):
    service = get_gdrive_service()
    if not service:
        return False
        
    try:
        folder_id = st.secrets.get("GDRIVE_FOLDER_ID", None)
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
        return True
    except Exception as e:
        print(f"Failed to download {gdrive_name} from Google Drive: {e}")
        return False
