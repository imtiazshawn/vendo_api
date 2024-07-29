from fastapi import FastAPI
from app.services.dbServices import connect_to_database
from app.database.init_db import initialize_roles

app = FastAPI()

@app.on_event("startup")
async def startup():
    await connect_to_database()
    await initialize_roles()
    print("DB Connect Successfully")
