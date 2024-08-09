from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from fastapi.security import OAuth2PasswordBearer

from app.cart.schemas import CartItemResponse, CartItemCreate
from app.auth.token import verify_token
from app.services.dbServices import connect_to_database
from app.utils.date_convert import format_datetime


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/admin/auth/login")

@router.get("/cart", response_model=List[CartItemResponse])
async def get_cart(token: str = Depends(oauth2_scheme)):
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

        cursor.execute("SELECT cartId FROM Carts WHERE userId=?", (user_id,))
        cart = cursor.fetchone()

        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

        cart_id = cart[0]

        cursor.execute("SELECT * FROM CartItems WHERE cartId=?", (cart_id,))
        cart_items = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "cart_item_id": item[0],
                "product_id": item[2],
                "quantity": item[3],
                "created_at": format_datetime(item[4]),
                "updated_at": format_datetime(item[5]),
            }
            for item in cart_items
        ]
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching cart")


@router.post("/cart", response_model=CartItemResponse)
async def add_to_cart(cart_item: CartItemCreate, token: str = Depends(oauth2_scheme)):
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

        cursor.execute("SELECT cartId FROM Carts WHERE userId=?", (user_id,))
        cart = cursor.fetchone()

        if not cart:
            cursor.execute("INSERT INTO Carts (userId, createdAt, updatedAt) VALUES (?, GETDATE(), GETDATE())", (user_id,))
            conn.commit()
            cursor.execute("SELECT cartId FROM Carts WHERE userId=?", (user_id,))
            cart = cursor.fetchone()

        cart_id = cart[0]

        cursor.execute("""
            INSERT INTO CartItems (cartId, productId, quantity, createdAt, updatedAt)
            VALUES (?, ?, ?, GETDATE(), GETDATE())
        """, (cart_id, cart_item.product_id, cart_item.quantity))
        conn.commit()

        cursor.execute("SELECT * FROM CartItems WHERE cartItemId=@@IDENTITY")
        new_cart_item = cursor.fetchone()

        cursor.close()
        conn.close()

        if not new_cart_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to add item to cart")

        return {
            "cart_item_id": new_cart_item[0],
            "product_id": new_cart_item[2],
            "quantity": new_cart_item[3],
            "created_at": format_datetime(new_cart_item[4]),
            "updated_at": format_datetime(new_cart_item[5]),
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error adding item to cart")



@router.put("/cart/{cart_item_id}", response_model=CartItemResponse)
async def update_cart_item(cart_item_id: int, quantity: int, token: str = Depends(oauth2_scheme)):
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
            SELECT ci.cartId FROM CartItems ci
            JOIN Carts c ON ci.cartId = c.cartId
            WHERE ci.cartItemId=? AND c.userId=?
        """, (cart_item_id, user_id))
        cart_item = cursor.fetchone()

        if not cart_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found or does not belong to user")

        cart_id = cart_item[0]

        cursor.execute("""
            UPDATE CartItems
            SET quantity=?, updatedAt=GETDATE()
            WHERE cartItemId=?
        """, (quantity, cart_item_id))
        conn.commit()

        cursor.execute("SELECT * FROM CartItems WHERE cartItemId=?", (cart_item_id,))
        updated_cart_item = cursor.fetchone()

        cursor.close()
        conn.close()

        if not updated_cart_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to update cart item")

        return {
            "cart_item_id": updated_cart_item[0],
            "product_id": updated_cart_item[2],
            "quantity": updated_cart_item[3],
            "created_at": format_datetime(updated_cart_item[4]),
            "updated_at": format_datetime(updated_cart_item[5]),
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating cart item")



@router.delete("/cart/{cart_item_id}")
async def remove_from_cart(cart_item_id: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM CartItems WHERE cartItemId=?", (cart_item_id,))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

        cursor.close()
        conn.close()

        return {"detail": "Item removed from cart successfully"}
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error removing item from cart")
