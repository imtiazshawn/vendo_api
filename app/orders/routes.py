from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from fastapi.security import OAuth2PasswordBearer

from app.orders.schemas import OrderResponse, OrderCreate
from app.auth.token import verify_token
from app.services.dbServices import connect_to_database
from app.utils.date_convert import format_datetime

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/admin/auth/login")


@router.get("/orders", response_model=List[OrderResponse])
async def get_user_orders(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT userId FROM Users WHERE username=?", (username,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user_id = user[0]

        cursor.execute("SELECT * FROM Orders WHERE userId=?", (user_id,))
        orders = cursor.fetchall()

        if not orders:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No orders found")

        order_list = []
        for order in orders:
            order_id, _, total_amount, status, created_at, updated_at = order

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



@router.post("/orders", response_model=OrderResponse)
async def add_order(order: OrderCreate, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT userId FROM Users WHERE username=?", (username,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user_id = user[0]

        cursor.execute("""
            INSERT INTO Orders (userId, totalAmount, status, createdAt, updatedAt)
            VALUES (?, ?, 'Pending', GETDATE(), GETDATE())
        """, (user_id, order.total_amount))
        conn.commit()

        cursor.execute("SELECT orderId FROM Orders WHERE orderId=@@IDENTITY")
        new_order_id = cursor.fetchone()[0]

        for item in order.items:
            cursor.execute("""
                INSERT INTO OrderItems (orderId, productId, quantity, price, createdAt, updatedAt)
                VALUES (?, ?, ?, ?, GETDATE(), GETDATE())
            """, (new_order_id, item.product_id, item.quantity, item.price))
        
        conn.commit()

        cursor.execute("""
            SELECT o.orderId, o.userId, o.totalAmount, o.status, o.createdAt, o.updatedAt, 
                   oi.productId, oi.quantity, oi.price
            FROM Orders o
            JOIN OrderItems oi ON o.orderId = oi.orderId
            WHERE o.orderId=?
        """, (new_order_id,))
        order_data = cursor.fetchall()

        if not order_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to create order")

        order_response = {
            "order_id": order_data[0][0],
            "user_id": order_data[0][1],
            "total_amount": order_data[0][2],
            "status": order_data[0][3],
            "created_at": format_datetime(order_data[0][4]),
            "updated_at": format_datetime(order_data[0][5]),
            "items": [
                {
                    "product_id": item[6],
                    "quantity": item[7],
                    "price": item[8]
                }
                for item in order_data
            ]
        }

        cursor.close()
        conn.close()

        return order_response
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating order")



@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_details(order_id: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT userId FROM Users WHERE username=?", (username,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user_id = user[0]

        cursor.execute("SELECT * FROM Orders WHERE orderId=? AND userId=?", (order_id, user_id))
        order = cursor.fetchone()

        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        order_id, _, total_amount, status, created_at, updated_at = order

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



@router.put("/orders/{order_id}/cancel")
async def cancel_order(order_id: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT userId FROM Users WHERE username=?", (username,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user_id = user[0]

        cursor.execute("SELECT * FROM Orders WHERE orderId=? AND userId=?", (order_id, user_id))
        order = cursor.fetchone()

        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

        cursor.execute("UPDATE Orders SET status='Cancelled', updatedAt=GETDATE() WHERE orderId=?", (order_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return {"detail": "Order cancelled successfully"}
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error cancelling order")
