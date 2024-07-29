import pypyodbc as odbc
from app.services.dbServices import connect_to_database

async def initialize_roles():
    conn = await connect_to_database()
    cursor = conn.cursor()

    conn.commit()
    cursor.close()
    conn.close()
