import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import discord
from discord.ext import commands
import sqlite3
from dotenv import load_dotenv
import pandas as pd
from discord import app_commands
from googleapiclient.errors import HttpError
import googleapiclient.errors
import asyncio

# Verificar si el archivo .env se carga correctamente
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Cargando variables desde: {dotenv_path}")
load_dotenv(dotenv_path)

# Escribir las credenciales en google_credentials.json desde la variable de entorno
credentials_content = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if credentials_content:
    try:
        with open("google_credentials.json", "w") as f:
            f.write(credentials_content)
            print("Archivo google_credentials.json creado correctamente.")
    except Exception as e:
        print(f"Error al crear el archivo google_credentials.json: {e}")
else:
    print("Error: La variable GOOGLE_APPLICATION_CREDENTIALS no contiene información válida.")


# Cargar las credenciales desde el archivo JSON
try:
    credentials = service_account.Credentials.from_service_account_file("google_credentials.json")
    drive_service = build('drive', 'v3', credentials=credentials)
    print("Credenciales de Google cargadas correctamente.")
except Exception as e:
    print(f"Error al cargar las credenciales de Google: {e}")

# Obtener las variables desde el archivo .env
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Verificar que las credenciales de Google están configuradas correctamente
if not GOOGLE_CREDENTIALS:
    print("Error: No se encontró la ruta de credenciales. Asegúrate de que GOOGLE_APPLICATION_CREDENTIALS está configurado en .env.")
    exit()
else:
    try:
        credentials_info = json.loads(GOOGLE_CREDENTIALS)
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        drive_service = build('drive', 'v3', credentials=credentials)
        print("Credenciales de Google cargadas correctamente.")
    except json.JSONDecodeError as e:
        print(f"Error al decodificar las credenciales de Google: {e}")
        exit()

# Definir los intents y configurar el bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # Necesario para leer los mensajes

# Crear el bot con los intents configurados
bot = commands.Bot(command_prefix='!', intents=intents)

# IDs de los roles para los diferentes comandos
PERMITIDOS_VERIFICARACCESO = [951995335583072276, 966445090954416179]
PERMITIDOS_GMAILSTAFF = [951651041454223402, 951995335583072276, 966445090954416179]
PERMITIDOS_SERIEABASE = [951995335583072276, 966445090954416179]
PERMITIDOS_CREARNUEVASERIE = [951995335583072276, 966445090954416179]
PERMITIDOS_CANAL = [951995335583072276, 966445090954416179]

# Crear el objeto CommandTree para slash commands
tree = bot.tree

# Conectar a la base de datos SQLite para miembros
def connect_db_members():
    try:
        conn = sqlite3.connect('members.db')
        print("Conexión a members.db exitosa.")
        return conn, conn.cursor()
    except Exception as e:
        print(f"Error al conectar a members.db: {e}")

# Conectar a la base de datos SQLite para proyectos
def connect_db_projects():
    try:
        conn = sqlite3.connect('proyectos.db')
        print("Conexión a proyectos.db exitosa.")
        return conn, conn.cursor()
    except Exception as e:
        print(f"Error al conectar a proyectos.db: {e}")

conn_members, cursor_members = connect_db_members()
conn_projects, cursor_projects = connect_db_projects()

# Crear las tablas si no existen en la base de datos de proyectos
cursor_projects.execute('''CREATE TABLE IF NOT EXISTS proyectos (folder_name TEXT, folder_id TEXT)''')
conn_projects.commit()

# Comando para verificar acceso a Google Drive
@tree.command(name="verificaracceso", description="Verificar acceso a Google Drive")
@commands.has_any_role(*PERMITIDOS_VERIFICARACCESO)
async def verificaracceso(interaction: discord.Interaction):
    try:
        main_folder_id = '1ulMXAlKKWEoiwYaG-wopI9aK1wEap9dJ'
        results = drive_service.files().list(q=f"'{main_folder_id}' in parents", pageSize=10, fields="files(id, name)", supportsAllDrives=True).execute()
        items = results.get('files', [])
        if not items:
            await interaction.response.send_message("La carpeta está vacía o el bot no tiene acceso a ella.")
        else:
            file_list = "\n".join([f"{item['name']} (ID: {item['id']})" for item in items])
            await interaction.response.send_message(f"Archivos en la carpeta:\n{file_list}")
    except googleapiclient.errors.HttpError as http_error:
        if http_error.resp.status == 403:
            await interaction.response.send_message("El bot no tiene permiso para acceder a esta carpeta.")
        elif http_error.resp.status == 404:
            await interaction.response.send_message("No se pudo encontrar la carpeta. Verifica que el ID de la carpeta es correcto.")
        else:
            await interaction.response.send_message(f"Error al acceder a Google Drive: {http_error}")
    except Exception as e:
        await interaction.response.send_message(f"Error inesperado: {e}")

# Comando para agregar un Gmail de un miembro a la base de datos
@tree.command(name="agregargmailstaff", description="Agregar Gmail de un miembro del staff")
@commands.has_any_role(*PERMITIDOS_GMAILSTAFF)
async def agregargmailstaff(interaction: discord.Interaction, user: discord.Member, gmail: str):
    cursor_members.execute("INSERT INTO members (discord_id, gmail) VALUES (?, ?)", (str(user.id), gmail))
    conn_members.commit()
    await interaction.response.send_message(f"Gmail '{gmail}' para el usuario {user.display_name} ha sido agregado.")

# Comando para mostrar todos los miembros con sus Gmails
@tree.command(name="mostrargmailstaff", description="Mostrar la lista de miembros registrados con su Gmail")
@commands.has_any_role(*PERMITIDOS_GMAILSTAFF)
async def mostrargmailstaff(interaction: discord.Interaction):
    cursor_members.execute("SELECT discord_id, gmail FROM members")
    members = cursor_members.fetchall()
    if not members:
        await interaction.response.send_message("No hay miembros registrados en la base de datos.")
    else:
        response = "\n".join([f"Discord ID: {member[0]}, Gmail: {member[1]}" for member in members])
        await interaction.response.send_message(f"Lista de miembros registrados:\n{response}")

# Comando para agregar una serie (carpeta) a la base de datos de proyectos
@tree.command(name="agregarserieabase", description="Agregar una serie y su ID de carpeta a la base de datos de proyectos")
@commands.has_any_role(*PERMITIDOS_SERIEABASE)
async def agregarserieabase(interaction: discord.Interaction, folder_name: str, folder_id: str):
    cursor_projects.execute("INSERT INTO proyectos (folder_name, folder_id) VALUES (?, ?)", (folder_name, folder_id))
    conn_projects.commit()
    await interaction.response.send_message(f"Carpeta '{folder_name}' con ID '{folder_id}' ha sido agregada a la base de datos de proyectos.")

# Función para obtener el correo del miembro desde la base de datos 'members.db'
def obtener_gmail_miembro(discord_id):
    cursor_members.execute("SELECT gmail FROM members WHERE discord_id = ?", (str(discord_id),))
    member = cursor_members.fetchone()
    if member:
        return member[0]
    return None

# Comando para agregar un miembro del staff a una serie en Google Drive
@tree.command(name="agregarstaffaldrive", description="Agregar un miembro del staff a una serie en Google Drive")
@app_commands.describe(user="El usuario de Discord", folder_name="El nombre de la serie", role="El rol (Colaborador o Lector)")
@app_commands.choices(
    role=[
        app_commands.Choice(name="Colaborador", value="writer"),
        app_commands.Choice(name="Lector", value="reader"),
    ]
)
async def agregarstaffaldrive(interaction: discord.Interaction, user: discord.Member, folder_name: str, role: app_commands.Choice[str]):
    await interaction.response.defer(ephemeral=True)

    try:
        gmail = obtener_gmail_miembro(user.id)
        if not gmail:
            await interaction.followup.send(f"No se encontró el Gmail para el usuario {user.display_name}.", ephemeral=True)
            return

        cursor_projects.execute("SELECT folder_id FROM proyectos WHERE folder_name = ?", (folder_name,))
        folder = cursor_projects.fetchone()

        if folder is None:
            await interaction.followup.send(f"No se encontró la serie '{folder_name}' en la base de datos.", ephemeral=True)
            return

        folder_id = folder[0]

        drive_permission = {
            'type': 'user',
            'role': role.value,
            'emailAddress': gmail
        }

        drive_service.permissions().create(
            fileId=folder_id,
            body=drive_permission,
            supportsAllDrives=True,
            sendNotificationEmail=True
        ).execute()

        await interaction.followup.send(f"Permisos de {role.name} otorgados a {user.display_name} en la serie '{folder_name}'.", ephemeral=True)
    
    except HttpError as error:
        await interaction.followup.send(f"Error al agregar los permisos en Google Drive: {error}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)

# Función de autocompletar para el campo folder_name
@agregarstaffaldrive.autocomplete('folder_name')
async def folder_name_autocomplete(interaction: discord.Interaction, current: str):
    series = await get_series_names()
    return [
        app_commands.Choice(name=serie, value=serie)
        for serie in series if current.lower() in serie.lower()
    ][:25]  # Discord limita a 25 resultados

# Función para obtener los nombres de las series para autocompletar
async def get_series_names():
    cursor_projects.execute("SELECT folder_name FROM proyectos")
    series = cursor_projects.fetchall()
    return [row[0] for row in series]

# Comando para agregar múltiples series desde un archivo Excel
@tree.command(name="agregarseriesmasivas", description="Agregar series masivamente desde un archivo Excel")
@commands.has_any_role(*PERMITIDOS_CREARNUEVASERIE)
async def agregarseriesmasivas(interaction: discord.Interaction, file: discord.Attachment):
    await interaction.response.defer()

    file_path = f"./{file.filename}"
    await file.save(file_path)

    try:
        df = pd.read_excel(file_path)

        if "nombre" not in df.columns or "id" not in df.columns:
            await interaction.followup.send("El archivo Excel debe contener las columnas 'nombre' y 'id'.")
            return

        for _, row in df.iterrows():
            nombre = row['nombre']
            folder_id = row['id']
            cursor_projects.execute("INSERT INTO proyectos (folder_name, folder_id) VALUES (?, ?)", (nombre, folder_id))

        conn_projects.commit()

        os.remove(file_path)

        await interaction.followup.send(f"Se han agregado {len(df)} series a la base de datos desde el archivo Excel.")
    
    except Exception as e:
        await interaction.followup.send(f"Error al agregar las series desde el archivo: {e}")

# Comando para crear una nueva serie de carpetas
@tree.command(name="crearnuevaserie", description="Crear una nueva carpeta en la unidad principal con subcarpetas")
@commands.has_any_role(*PERMITIDOS_CREARNUEVASERIE)
async def crearnuevaserie(interaction: discord.Interaction, folder_name: str):
    await interaction.response.defer()

    main_folder_id = '1ulMXAlKKWEoiwYaG-wopI9aK1wEap9dJ'
    try:
        new_folder_id = create_folder(folder_name, main_folder_id)
        create_folder('Raws', new_folder_id)
        create_folder('Traducciones', new_folder_id)
        create_folder('Terminados', new_folder_id)
        create_folder('Limpieza', new_folder_id)

        cursor_projects.execute("INSERT INTO proyectos (folder_name, folder_id) VALUES (?, ?)", (folder_name, new_folder_id))
        conn_projects.commit()

        folder_url = f"https://drive.google.com/drive/folders/{new_folder_id}"

        await interaction.followup.send(f"Carpeta '{folder_name}' creada y agregada a la base de datos.\nAccede a ella aquí: {folder_url}")
        
    except Exception as e:
        await interaction.followup.send(f"Error al crear la serie de carpetas: {e}")

# Función auxiliar para crear una carpeta en Google Drive
def create_folder(name, parent_id=None):
    folder_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id] if parent_id else []
    }
    folder = drive_service.files().create(body=folder_metadata, fields='id', supportsAllDrives=True).execute()
    return folder['id']

# Comando para mostrar todas las series con paginación
@tree.command(name="mostrarproyectos", description="Mostrar las series agregadas a la base de datos")
@commands.has_any_role(*PERMITIDOS_VERIFICARACCESO)
async def mostrarproyectos(interaction: discord.Interaction, page: int = 1):
    try:
        cursor_projects.execute("SELECT folder_name, folder_id FROM proyectos")
        proyectos = cursor_projects.fetchall()

        if not proyectos:
            await interaction.response.send_message("No hay series registradas en la base de datos.")
            return

        items_per_page = 10
        total_pages = (len(proyectos) + items_per_page - 1) // items_per_page

        if page < 1 or page > total_pages:
            await interaction.response.send_message(f"Página inválida. Hay {total_pages} páginas en total.")
            return

        start = (page - 1) * items_per_page
        end = start + items_per_page
        page_projects = proyectos[start:end]

        response = f"**Página {page}/{total_pages}**\n"
        for folder_name, folder_id in page_projects:
            response += f"- **{folder_name}** (ID: `{folder_id}`)\n"

        await interaction.response.send_message(response)

    except Exception as e:
        await interaction.response.send_message(f"Error al obtener las series de la base de datos: {e}")

# Cerrar la conexión a la base de datos cuando el bot se desconecta
@bot.event
async def on_disconnect():
    conn_members.close()
    conn_projects.close()

@bot.event
async def on_ready():
    try:
        await asyncio.sleep(2)
        await bot.tree.sync()
        print("Comandos globales sincronizados correctamente.")
    except Exception as e:
        print(f"Error al sincronizar los comandos: {e}")

# Iniciar el bot con el token
try:
    bot.run(DISCORD_TOKEN)
finally:
    conn_members.close()
    conn_projects.close()
    print("Conexiones a las bases de datos cerradas.")
