from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Optional

from app.products.schemas import ProductCreate, ProductUpdate, ProductResponse
from app.services.dbServices import connect_to_database
from app.utils import format_datetime

router = APIRouter()

@router.get("/products", response_model=List[ProductResponse])
async def get_all_products(
    name: Optional[str] = Query(None, description="Filter products by name"),
    min_price: Optional[float] = Query(None, description="Filter products by minimum price"),
    max_price: Optional[float] = Query(None, description="Filter products by maximum price")
):
    try:
        conn = await connect_to_database()
        cursor = conn.cursor()
        
        query = "SELECT * FROM Products WHERE 1=1"
        params = []
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)
        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)
        
        cursor.execute(query, params)
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching products")
    


@router.get("/products/{productId}", response_model=ProductResponse)
async def get_product_details(productId: int):
    try:
        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Products WHERE productId=?", (productId,))
        product = cursor.fetchone()

        cursor.close()
        conn.close()

        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        return {
            "id": product[0],
            "name": product[1],
            "description": product[2],
            "price": product[3],
            "category_id": product[4],
            "image_url": product[5],
            "created_at": format_datetime(product[6]),
            "updated_at": format_datetime(product[7])
        }
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching product details")



@router.post("/products", response_model=ProductResponse)
async def create_product(product: ProductCreate):
    try:
        conn = await connect_to_database()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO Products (name, description, price, categoryId, imageUrl, createdAt, updatedAt)
            VALUES (?, ?, ?, ?, ?, GETDATE(), GETDATE())
        """, (product.name, product.description, product.price, product.category_id, product.image_url))
        conn.commit()
        
        cursor.execute("SELECT * FROM Products WHERE productId=@@IDENTITY")
        new_product = cursor.fetchone()
        
        cursor.close()
        conn.close()

        if not new_product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product creation failed")

        return {
            "id": new_product[0],
            "name": new_product[1],
            "description": new_product[2],
            "price": new_product[3],
            "category_id": new_product[4],
            "image_url": new_product[5],
            "created_at": format_datetime(new_product[6]),
            "updated_at": format_datetime(new_product[7]),
        }
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating product")


    
@router.put("/products/{productId}", response_model=ProductResponse)
async def update_product(productId: int, product: ProductUpdate):
    try:
        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE Products
            SET name=?, description=?, price=?, categoryId=?, imageUrl=?, updatedAt=GETDATE()
            WHERE productId=?
        """, (product.name, product.description, product.price, product.category_id, product.image_url, productId))
        conn.commit()

        cursor.execute("SELECT * FROM Products WHERE productId=?", (productId,))
        updated_product = cursor.fetchone()

        cursor.close()
        conn.close()

        if not updated_product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        return {
            "id": updated_product[0],
            "name": updated_product[1],
            "description": updated_product[2],
            "price": updated_product[3],
            "category_id": updated_product[4],
            "image_url": updated_product[5],
            "created_at": format_datetime(updated_product[6]),
            "updated_at": format_datetime(updated_product[7])
        }
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error updating product")



@router.delete("/products/{productId}")
async def delete_product(productId: int):
    try:
        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM Products WHERE productId=?", (productId,))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        cursor.close()
        conn.close()

        return {"detail": "Product deleted successfully"}
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting product")