from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from fastapi.security import OAuth2PasswordBearer

from app.auth.token import verify_token
from app.services.dbServices import connect_to_database
from app.utils.date_convert import format_datetime
from app.utils.is_admin import is_admin
from app.orders.schemas import OrderResponse

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/admin/auth/login")

@router.get("/admin/orders", response_model=List[OrderResponse])
async def get_all_orders(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Orders")
        orders = cursor.fetchall()

        if not orders:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No orders found")

        order_list = []
        for order in orders:
            order_id, user_id, total_amount, status, created_at, updated_at = order

            cursor.execute("SELECT productId, quantity, price FROM OrderItems WHERE orderId=?", (order_id,))
            items = cursor.fetchall()

            order_list.append({
                "order_id": order_id,
                "user_id": user_id,
                "total_amount": total_amount,
                "status": status,
                "created_at": format_datetime(created_at),
                "updated_at": format_datetime(updated_at),
                "items": [
                    {
                        "product_id": item[0],
                        "quantity": item[1],
                        "price": item[2]
                    }
                    for item in items
                ]
            })

        cursor.close()
        conn.close()

        return order_list
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching orders")


@router.get("/admin/orders/{order_id}", response_model=OrderResponse)
async def get_order_details(order_id: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Orders WHERE orderId=?", (order_id,))
        order = cursor.fetchone()

        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        order_id, user_id, total_amount, status, created_at, updated_at = order

        cursor.execute("SELECT productId, quantity, price FROM OrderItems WHERE orderId=?", (order_id,))
        items = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "order_id": order_id,
            "user_id": user_id,
            "total_amount": total_amount,
            "status": status,
            "created_at": format_datetime(created_at),
            "updated_at": format_datetime(updated_at),
            "items": [
                {
                    "product_id": item[0],
                    "quantity": item[1],
                    "price": item[2]
                }
                for item in items
            ]
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching order details")


@router.put("/admin/orders/{order_id}/status")
async def update_order_status(order_id: int, status: str, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        if status not in ["Pending", "Completed", "Cancelled"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Orders WHERE orderId=?", (order_id,))
        order = cursor.fetchone()

        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        cursor.execute("UPDATE Orders SET status=?, updatedAt=GETDATE() WHERE orderId=?", (status, order_id))
        conn.commit()

        cursor.close()
        conn.close()

        return {"detail": "Order status updated successfully"}
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating order status")
