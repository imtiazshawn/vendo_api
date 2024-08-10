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
from app.orders.routes import router as orders_router
from app.admin.orders_routes import router as admin_order_router
from app.payments.routes import router as payments_router
from app.reviews.routes import router as reviews_router
from app.inventory.routes import router as inventory_routes
from app.notifications.routes import router as notifications_routes
from app.reports.routes import router as reports_routes

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
app.include_router(orders_router, prefix="/api", tags=["Orders"])
app.include_router(admin_order_router, prefix="/api", tags=["Admin Order Management"])
app.include_router(payments_router, prefix="/api", tags=["Payments"])
app.include_router(reviews_router, prefix="/api", tags=["Reviews"])
app.include_router(inventory_routes, prefix="/api", tags=["Inventory"])
app.include_router(notifications_routes, prefix="/api", tags=["Notifications"])
app.include_router(reports_routes, prefix="/api", tags=["Reports"])