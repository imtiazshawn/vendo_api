from fastapi import FastAPI

from app.services.dbServices import connect_to_database
from app.database.init_db import initialize_roles
from app.auth.routes import router as auth_router
from app.auth.admin_routes import router as admin_auth_router
from app.user.routes import router as user_router
from app.admin.routes import router as admin_router
from app.products.routes import router as product_router
from app.categories.routes import router as categories_router
from app.cart.routes import router as cart_router

app = FastAPI(
    title="VendoAPI"
)

@app.on_event("startup")
async def startup():
    await connect_to_database()
    await initialize_roles()
    print("DB Connect Successfully")

app.include_router(auth_router, prefix="/api/auth", tags=["User Auth"])
app.include_router(user_router, prefix="/api/user", tags=["User Management"])
app.include_router(admin_auth_router, prefix="/api/admin/auth", tags=["Admin Auth"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin Management"])
app.include_router(categories_router, prefix="/api", tags=["Categories"])
app.include_router(product_router, prefix="/api", tags=["Products"])
app.include_router(cart_router, prefix="/api", tags=["Carts"])