import sqlite3
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

# Autenticación con las credenciales del archivo JSON de Google
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
SCOPES = ['https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# Conectar a la base de datos para obtener el folder_id
def get_folder_id_from_db(folder_name):
    conn = sqlite3.connect('idseries.db')
    cursor = conn.cursor()
    cursor.execute("SELECT folder_id FROM series WHERE folder_name = ?", (folder_name,))
    folder_id = cursor.fetchone()
    conn.close()
    return folder_id[0] if folder_id else None

# Obtener las subcarpetas de Google Drive
def get_subfolders_from_drive(folder_id):
    try:
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder'",
            pageSize=1000,
            fields="files(id, name)"
        ).execute()
        return results.get('files', [])
    except Exception as e:
        print(f"Error al obtener subcarpetas: {e}")
        return []

# Guardar los datos en un archivo Excel
def save_to_excel(folder_name, folder_id):
    subfolders = get_subfolders_from_drive(folder_id)
    data = [(folder['name'], folder['id']) for folder in subfolders]
    df = pd.DataFrame(data, columns=['nombre', 'id'])
    excel_file = f"{folder_name}_subfolders.xlsx"
    df.to_excel(excel_file, index=False)
    print(f"Archivo Excel guardado: {excel_file}")

if __name__ == "__main__":
    folder_name = input("Introduce el nombre de la carpeta: ")
    folder_id = get_folder_id_from_db(folder_name)
    
    if folder_id:
        save_to_excel(folder_name, folder_id)
    else:
        print(f"No se encontró la carpeta '{folder_name}' en la base de datos.")
