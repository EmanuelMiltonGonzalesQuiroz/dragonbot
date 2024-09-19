from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import pandas as pd
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)

# Ruta a la base de datos donde se guardarán los IDs de las carpetas
DB_PATH = 'idseries.db'

# Inicialización de la API de Google Drive
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Inicializar las credenciales de Google Drive
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# Ruta para la página principal
@app.route('/')
def index():
    # Conectarse a la base de datos y obtener las carpetas guardadas
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT folder_name, folder_id FROM series")
    folders = cursor.fetchall()
    conn.close()
    return render_template('index.html', folders=folders)

# Ruta para agregar una carpeta a la base de datos
@app.route('/add_folder', methods=['POST'])
def add_folder():
    folder_name = request.form['folder_name']
    folder_id = request.form['folder_id']

    # Guardar el nombre e ID en la base de datos
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO series (folder_name, folder_id) VALUES (?, ?)", (folder_name, folder_id))
    conn.commit()
    conn.close()
    return redirect('/')

# Ruta para descargar los nombres e IDs en un archivo Excel
@app.route('/download_excel', methods=['POST'])
def download_excel():
    folder_name = request.form['folder_name']  # Obtener el nombre de la carpeta seleccionada
    folder_id = request.form['folder_id']  # Obtener el ID de la carpeta seleccionada

    try:
        # Ejecutar la consulta en Google Drive para las subcarpetas
        query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
        print(f"Ejecutando consulta en Google Drive: {query}")

        # Modificamos supportsAllDrives a True para unidades compartidas
        results = drive_service.files().list(q=query, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        items = results.get('files', [])

        if not items:
            return "No se encontraron subcarpetas."

        # Preparar los datos reales de Google Drive para el Excel
        carpetas = [{"Nombre": item['name'], "ID": item['id']} for item in items]
        df = pd.DataFrame(carpetas)

        # Guardar el DataFrame en un archivo Excel
        excel_path = 'series_con_id.xlsx'
        df.to_excel(excel_path, index=False)

        # Enviar el archivo Excel al usuario
        return send_file(excel_path, as_attachment=True)

    except HttpError as error:
        return f"Error al acceder a Google Drive: {error}"

    except Exception as e:
        return f"Error al generar el archivo Excel: {e}"


if __name__ == '__main__':
    app.run(debug=True)
