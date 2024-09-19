import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('idseries.db')
cursor = conn.cursor()

# Obtener la estructura de la tabla 'series'
cursor.execute("PRAGMA table_info(series)")
columns = cursor.fetchall()

# Mostrar la estructura de la tabla
print("Columnas de la tabla 'series':")
for column in columns:
    print(column)

conn.close()
