from app.services.dbServices import connect_to_database

async def is_admin(username: str) -> bool:
    conn = await connect_to_database()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM Admins WHERE username=?", (username,))
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists