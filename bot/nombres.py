import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd

# Ruta del archivo de credenciales
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Configuración de los alcances de Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Autenticación con las credenciales del archivo JSON
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# ID de la carpeta principal donde están las subcarpetas
main_folder_id = '1ulMXAlKKWEoiwYaG-wopI9aK1wEap9dJ'

def obtener_carpetas_y_guardar_en_excel(folder_id):
    try:
        # Realizar la consulta para listar las carpetas dentro de la carpeta principal
        query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        
        # Añadimos el parámetro 'includeItemsFromAllDrives=True' para incluir unidades compartidas
        results = drive_service.files().list(
            q=query, 
            fields="files(id, name)", 
            supportsAllDrives=True, 
            includeItemsFromAllDrives=True
        ).execute()

        items = results.get('files', [])

        if not items:
            print("No se encontraron carpetas ni archivos en la carpeta principal.")
        else:
            # Crear una lista para almacenar los nombres e IDs de las carpetas
            carpetas = []
            for item in items:
                print(f"Elemento encontrado: {item['name']} (ID: {item['id']})")
                carpetas.append({"nombre": item['name'], "id": item['id']})

            # Convertir la lista a un DataFrame de pandas
            df = pd.DataFrame(carpetas)

            # Guardar el DataFrame en un archivo Excel
            output_file = "carpetas_drive.xlsx"
            df.to_excel(output_file, index=False)
            print(f"Archivo Excel '{output_file}' guardado correctamente.")

    except Exception as e:
        print(f"Error al obtener las carpetas de Google Drive: {e}")

# Ejecutar la función para obtener las carpetas y guardar en Excel
obtener_carpetas_y_guardar_en_excel(main_folder_id)
