from app.services.dbServices import connect_to_database

async def initialize_roles():
    conn = await connect_to_database()
    cursor = conn.cursor()

    # Ensure roles table exists
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='roles' and xtype='U')
    CREATE TABLE roles (
        id INT PRIMARY KEY IDENTITY(1,1),
        name VARCHAR(50) NOT NULL
    )
    """)

    # Insert default roles if they do not exist
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM roles WHERE name='admin')
    INSERT INTO roles (name) VALUES ('admin')
    """)
    cursor.execute("""
    IF NOT EXISTS (SELECT * FROM roles WHERE name='user')
    INSERT INTO roles (name) VALUES ('user')
    """)

    conn.commit()
    cursor.close()
    conn.close()
