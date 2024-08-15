import os
import json
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the service account JSON from environment variables
SERVICE_ACCOUNT_JSON = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))

# Define the scopes required for the API
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_google_drive():
    """
    Authenticate and build the Google Drive service.
    
    Returns:
        googleapiclient.discovery.Resource: The Google Drive service instance.
    """
    credentials = service_account.Credentials.from_service_account_info(
        SERVICE_ACCOUNT_JSON, scopes=SCOPES)
    service = build('drive', 'v3', credentials=credentials)
    return service

def list_files(service, folder_id):
    """
    List files in a specified Google Drive folder.

    Args:
        service (googleapiclient.discovery.Resource): The Google Drive service instance.
        folder_id (str): The ID of the Google Drive folder to list files from.

    Returns:
        list: A list of file metadata dictionaries.
    """
    try:
        query = f"'{folder_id}' in parents"
        print(f"Running query: {query}")  # Debugging information
        results = service.files().list(q=query, pageSize=10, fields="nextPageToken, files(id, name)").execute()
        files = results.get('files', [])

        if not files:
            print('No files found in the folder.')
        else:
            print('Files in folder:')
            for file in files:
                print(f'{file["name"]} ({file["id"]})')
        return files
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def download_files(service, files):
    """
    Download multiple files from Google Drive.

    Args:
        service (googleapiclient.discovery.Resource): The Google Drive service instance.
        files (list): A list of file metadata dictionaries.
    """
    for file in files:
        file_id = file['id']
        file_name = file['name']
        try:
            request = service.files().get_media(fileId=file_id)
            with io.FileIO(file_name, 'wb') as file_handle:
                downloader = MediaIoBaseDownload(file_handle, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    print(f"Downloading {file_name}: {int(status.progress() * 100)}% complete.")
            print(f"{file_name} downloaded successfully.")
        except HttpError as error:
            print(f"An error occurred while downloading {file_name}: {error}")

if __name__ == '__main__':
    drive_service = authenticate_google_drive()
    folder_id = '1M8bglL4H1CYPooW7b8PyBhdCmsxYQDuX'
    files = list_files(drive_service, folder_id)  # List files in the specified folder
    
    if files:
        download_files(drive_service, files)  # Download all files in the list
    else:
        print("No files to download.")
