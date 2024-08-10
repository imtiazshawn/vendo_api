from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import List

from app.auth.token import verify_token
from app.services.dbServices import connect_to_database
from app.utils.is_admin import is_admin
from app.inventory.schemas import InventoryResponse, InventoryUpdate, InitialInventory
from app.utils.date_convert import format_datetime

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/admin/auth/login")

@router.get("/inventory", response_model=List[InventoryResponse])
async def get_inventory(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Inventory")
        inventory_items = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "inventory_id": item[0],
                "product_id": item[1],
                "quantity": item[2],
                "created_at": format_datetime(item[3]),
                "updated_at": format_datetime(item[4]),
            }
            for item in inventory_items
        ]
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching inventory")

@router.put("/inventory/{product_id}", response_model=InventoryResponse)
async def update_inventory(product_id: int, inventory_update: InventoryUpdate, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Inventory WHERE productId=?", (product_id,))
        existing_inventory = cursor.fetchone()

        if not existing_inventory:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory record not found")

        cursor.execute(
            """
            UPDATE Inventory
            SET quantity=?, updatedAt=GETDATE()
            WHERE productId=?
        """,
            (inventory_update.quantity, product_id),
        )
        conn.commit()

        cursor.execute("SELECT * FROM Inventory WHERE productId=?", (product_id,))
        updated_inventory = cursor.fetchone()

        cursor.close()
        conn.close()

        if not updated_inventory:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to update inventory")

        return {
            "inventory_id": updated_inventory[0],
            "product_id": updated_inventory[1],
            "quantity": updated_inventory[2],
            "created_at": format_datetime(updated_inventory[3]),
            "updated_at": format_datetime(updated_inventory[4]),
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating inventory")


@router.post("/initialize_inventory", response_model=List[InventoryResponse])
async def initialize_inventory(initial_inventory: List[InitialInventory], token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        for item in initial_inventory:
            cursor.execute(
                """
                MERGE INTO Inventory AS target
                USING (VALUES (?, ?)) AS source (productId, quantity)
                ON target.productId = source.productId
                WHEN MATCHED THEN
                    UPDATE SET quantity = source.quantity, updatedAt = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT (productId, quantity, createdAt, updatedAt)
                    VALUES (source.productId, source.quantity, GETDATE(), GETDATE());
                """,
                (item.product_id, item.quantity),
            )

        conn.commit()

        cursor.execute("SELECT * FROM Inventory")
        inventory_items = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "inventory_id": item[0],
                "product_id": item[1],
                "quantity": item[2],
                "created_at": format_datetime(item[3]),
                "updated_at": format_datetime(item[4]),
            }
            for item in inventory_items
        ]
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error initializing inventory")