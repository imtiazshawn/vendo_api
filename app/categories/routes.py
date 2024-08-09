from fastapi import APIRouter, HTTPException, status
from typing import List

from app.categories.schemas import CategoryCreate, CategoryUpdate, CategoryResponse
from app.products.schemas import ProductResponse
from app.services.dbServices import connect_to_database
from app.utils import format_datetime

router = APIRouter()

@router.get("/categories", response_model=List[CategoryResponse])
async def get_all_categories():
    try:
        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Categories")
        categories = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "id": category[0],
                "name": category[1]
            }
            for category in categories
        ]
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching categories")

@router.get("/categories/{categoryId}/products", response_model=List[ProductResponse])
async def get_products_by_category(categoryId: int):
    try:
        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Products WHERE categoryId=?", (categoryId,))
        products = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "id": product[0],
                "name": product[1],
                "description": product[2],
                "price": product[3],
                "category_id": product[4],
                "image_url": product[5],
                "created_at": format_datetime(product[6]),
                "updated_at": format_datetime(product[7])
            }
            for product in products
        ]
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching products by category")



@router.post("/categories", response_model=CategoryResponse)
async def create_category(category: CategoryCreate):
    try:
        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Categories (name)
            VALUES (?)
        """, (category.name,))
        conn.commit()

        cursor.execute("SELECT * FROM Categories WHERE categoryId=@@IDENTITY")
        new_category = cursor.fetchone()

        cursor.close()
        conn.close()

        if not new_category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category creation failed")

        return {
            "id": new_category[0],
            "name": new_category[1]
        }
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating category")

@router.put("/categories/{categoryId}", response_model=CategoryResponse)
async def update_category(categoryId: int, category: CategoryUpdate):
    try:
        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE Categories
            SET name=?
            WHERE categoryId=?
        """, (category.name, categoryId))
        conn.commit()

        cursor.execute("SELECT * FROM Categories WHERE categoryId=?", (categoryId,))
        updated_category = cursor.fetchone()

        cursor.close()
        conn.close()

        if not updated_category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        return {
            "id": updated_category[0],
            "name": updated_category[1]
        }
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating category")

@router.delete("/categories/{categoryId}")
async def delete_category(categoryId: int):
    try:
        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM Categories WHERE categoryId=?", (categoryId,))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        cursor.close()
        conn.close()

        return {"detail": "Category deleted successfully"}
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting category")