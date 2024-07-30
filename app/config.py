from fastapi import FastAPI
from app.services.dbServices import connect_to_database
from app.database.init_db import initialize_roles
from app.auth.routes import router as auth_router

app = FastAPI()

@app.on_event("startup")
async def startup():
    await connect_to_database()
    await initialize_roles()
    print("DB Connect Successfully")

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
