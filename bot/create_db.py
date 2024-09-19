import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('idseries.db')
cursor = conn.cursor()

# Crear la tabla para almacenar los IDs de las carpetas
cursor.execute('''
CREATE TABLE IF NOT EXISTS series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_name TEXT NOT NULL,
    folder_id TEXT NOT NULL
)
''')

# Guardar cambios y cerrar la conexión
conn.commit()
conn.close()
