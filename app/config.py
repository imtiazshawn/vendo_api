from fastapi import FastAPI
from app.services.dbServices import connect_to_database
from app.database.init_db import initialize_roles
from app.auth.routes import router as auth_router
from app.auth.admin_routes import router as admin_auth_router

app = FastAPI(
    title="VendoAPI"
)

@app.on_event("startup")
async def startup():
    await connect_to_database()
    await initialize_roles()
    print("DB Connect Successfully")

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(admin_auth_router, prefix="/api/admin/auth", tags=["admin_auth"])
