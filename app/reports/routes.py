from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Any, Dict, Union
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta

from app.auth.token import verify_token
from app.services.dbServices import connect_to_database
from app.utils.is_admin import is_admin
from app.reports.schemas import SalesReport, OrderReport, UserActivityReport
from app.utils.date_convert import format_datetime

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/admin/auth/login")

@router.get("/admin/reports/sales-report")
async def get_sales_report(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        query = """
        SELECT p.productId, p.name AS product_name, SUM(oi.quantity * p.price) AS total_sales
        FROM OrderItems oi
        JOIN Products p ON oi.productId = p.productId
        GROUP BY p.productId, p.name
        ORDER BY total_sales DESC
        """
        cursor.execute(query)
        sales_data = cursor.fetchall()

        total_sales = sum(item[2] for item in sales_data)

        chart_data = [float(item[2]) for item in sales_data]

        cursor.close()
        conn.close()

        return {
            "total_sales": f"${total_sales:,.2f}",
            "chartData": chart_data
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching sales report")
    

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


@router.get("/admin/reports/orders-report", response_model=Dict[str, Union[str, List[int]]])
async def get_orders_report(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        if conn is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database connection failed")

        cursor = conn.cursor()

        now = datetime.now()
        first_day_of_month = now.replace(day=1)
        last_day_of_month = (now.replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        formatted_start_date = first_day_of_month.strftime('%Y-%m-%d')
        formatted_end_date = last_day_of_month.strftime('%Y-%m-%d')

        query = """
        SELECT FORMAT(o.createdAt, 'yyyy-MM-dd') AS period, COUNT(o.orderId) AS total_orders
        FROM Orders o
        WHERE o.createdAt >= ? AND o.createdAt <= ?
        GROUP BY FORMAT(o.createdAt, 'yyyy-MM-dd')
        ORDER BY period
        """
        
        cursor.execute(query, (formatted_start_date, formatted_end_date))
        order_data = cursor.fetchall()

        cursor.close()
        conn.close()

        days_in_month = [(first_day_of_month + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((last_day_of_month - first_day_of_month).days + 1)]
        total_orders = {row[0]: int(row[1]) for row in order_data}
        chart_data = [total_orders.get(day, 0) for day in days_in_month]

        return {
            "total_orders": str(sum(chart_data)),
            "chartData": chart_data
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching orders report")



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


@router.get("/admin/reports/users-report", response_model=Dict[str, Union[str, List[float]]])
async def get_users_report(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        query = """
        SELECT FORMAT(createdAt, 'yyyy-MM') AS period, COUNT(userId) AS user_count
        FROM Users
        GROUP BY FORMAT(createdAt, 'yyyy-MM')
        ORDER BY period
        """
        cursor.execute(query)
        user_data = cursor.fetchall()

        cursor.close()
        conn.close()

        user_counts = [float(item[1]) for item in user_data]

        return {
            "total_users": f"{sum(user_counts):,}",
            "chartData": user_counts
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching users report")
    

@router.post("/record-visit", response_model=Dict[str, str])
async def record_visit(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        query = """
        INSERT INTO UserVisits (userId, createdAt)
        VALUES ((SELECT userId FROM Users WHERE username = ?), GETDATE())
        """
        cursor.execute(query, (username,))
        conn.commit()

        cursor.close()
        conn.close()

        return {"message": "Visit recorded successfully"}
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error recording visit")


@router.get("/admin/reports/visitors", response_model=Dict[str, Union[str, List[float]]])
async def get_visitors_report(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        query = """
        SELECT FORMAT(createdAt, 'yyyy-MM') AS period, COUNT(userId) AS visitor_count
        FROM UserVisits
        GROUP BY FORMAT(createdAt, 'yyyy-MM')
        ORDER BY period
        """
        cursor.execute(query)
        visitor_data = cursor.fetchall()

        cursor.close()
        conn.close()

        visitor_counts = [float(item[1]) for item in visitor_data]

        return {
            "total_visitors": f"{sum(visitor_counts):,}",
            "chartData": visitor_counts
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching visitors report")
