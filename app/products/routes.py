from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Optional

from app.products.schemas import ProductResponse
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
