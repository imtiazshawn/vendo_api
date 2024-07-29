import os
from dotenv import load_dotenv
import pypyodbc as odbc

load_dotenv()

DRIVER_NAME = "SQL SERVER"
SERVER_NAME = os.getenv("DATABASE_SERVER")
DATABASE_NAME = os.getenv("DATABASE_NAME")

connection_string = f"""
    DRIVER={{{DRIVER_NAME}}};
    SERVER={SERVER_NAME};
    DATABASE={DATABASE_NAME};
"""

async def connect_to_database():
    try:
        conn = odbc.connect(connection_string)
        print("Database connection successful")
        return conn
    except Exception as e:
        print("Database connection failed")
        print(e)
        return None
