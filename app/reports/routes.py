from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from fastapi.security import OAuth2PasswordBearer

from app.auth.token import verify_token
from app.services.dbServices import connect_to_database
from app.utils.is_admin import is_admin
from app.reports.schemas import SalesReport, OrderReport, UserActivityReport
from app.utils.date_convert import format_datetime

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/admin/auth/login")

@router.get("/admin/reports/sales", response_model=List[SalesReport])
async def get_sales_report(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        query = """
        SELECT p.productId, p.name, SUM(oi.quantity * p.price) AS total_sales
        FROM OrderItems oi
        JOIN Products p ON oi.productId = p.productId
        GROUP BY p.productId, p.name
        """
        cursor.execute(query)
        sales_data = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "product_id": item[0],
                "product_name": item[1],
                "total_sales": float(item[2])
            }
            for item in sales_data
        ]
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching sales report")

@router.get("/admin/reports/orders", response_model=List[OrderReport])
async def get_order_report(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        query = """
        SELECT o.orderId, o.userId, SUM(oi.quantity * oi.price) AS total_amount, o.createdAt
        FROM Orders o
        JOIN OrderItems oi ON o.orderId = oi.orderId
        GROUP BY o.orderId, o.userId, o.createdAt
        """
        cursor.execute(query)
        order_data = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "order_id": item[0],
                "user_id": item[1],
                "total_amount": float(item[2]),
                "order_date": format_datetime(item[3])
            }
            for item in order_data
        ]
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching order report")
    

@router.get("/admin/reports/users", response_model=List[UserActivityReport])
async def get_user_activity_report(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        query = """
        SELECT u.userId, u.username, COUNT(o.orderId) AS total_orders, COALESCE(SUM(oi.quantity * p.price), 0) AS total_amount_spent
        FROM Users u
        LEFT JOIN Orders o ON u.userId = o.userId
        LEFT JOIN OrderItems oi ON o.orderId = oi.orderId
        LEFT JOIN Products p ON oi.productId = p.productId
        GROUP BY u.userId, u.username
        """
        cursor.execute(query)
        user_activity_data = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "user_id": item[0],
                "username": item[1],
                "total_orders": item[2],
                "total_amount_spent": float(item[3]) if item[3] is not None else 0.0
            }
            for item in user_activity_data
        ]
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching user activity report")

