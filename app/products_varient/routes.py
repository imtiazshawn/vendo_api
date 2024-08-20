from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from fastapi.security import OAuth2PasswordBearer

from app.products_varient.schemas import (
    ProductResponse,
    VariantTypeCreate,
    VariantTypeUpdate,
    VariantResponse,
    ProductVariantCreate,
    ProductVariantUpdate
)
from app.services.dbServices import connect_to_database
from app.utils.date_convert import format_datetime
from app.utils.is_admin import is_admin
from app.auth.token import verify_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/admin/auth/login")

@router.get("/variant-types/{categoryId}", response_model=List[VariantTypeCreate])
async def get_variant_types_by_category(categoryId: int):
    try:
        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM VariantTypes WHERE categoryId=?", (categoryId,))
        variant_types = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {"variantTypeId": vt[0], "categoryId": vt[1], "variantType": vt[2]}
            for vt in variant_types
        ]
    except Exception as e:
        print("Exception:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching variant types",
        )

@router.post("/variant-types", response_model=VariantTypeCreate)
async def create_variant_type(
    variant_type: VariantTypeCreate, token: str = Depends(oauth2_scheme)
):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
            )

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO VariantTypes (categoryId, variantType)
            VALUES (?, ?)
        """,
            (variant_type.categoryId, variant_type.variantType),
        )
        conn.commit()

        cursor.execute("SELECT * FROM VariantTypes WHERE variantTypeId=@@IDENTITY")
        new_variant_type = cursor.fetchone()

        cursor.close()
        conn.close()

        if not new_variant_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Variant Type creation failed"
            )

        return {
            "variantTypeId": new_variant_type[0],
            "categoryId": new_variant_type[1],
            "variantType": new_variant_type[2]
        }
    except Exception as e:
        print("Exception:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or error creating variant type",
        )

@router.put("/variant-types/{variantTypeId}", response_model=VariantTypeUpdate)
async def update_variant_type(variantTypeId: int, variant_type: VariantTypeUpdate, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get('sub')
        
        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE VariantTypes
            SET variantType=?
            WHERE variantTypeId=?
            """,
            (variant_type.variantType, variantTypeId),
        )
        conn.commit()

        cursor.execute("SELECT * FROM VariantTypes WHERE variantTypeId=?", (variantTypeId,))
        updated_variant_type = cursor.fetchone()

        cursor.close()
        conn.close()

        if not updated_variant_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Variant Type not found"
            )

        return {
            "variantTypeId": updated_variant_type[0],
            "categoryId": updated_variant_type[1],
            "variantType": updated_variant_type[2]
        }
    except Exception as e:
        print("Exception:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or error updating variant type",
        )

@router.delete("/variant-types/{variantTypeId}")
async def delete_variant_type(variantTypeId: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get('sub')
        
        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM VariantTypes WHERE variantTypeId=?", (variantTypeId,))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Variant Type not found"
            )

        cursor.close()
        conn.close()

        return {"detail": "Variant Type deleted successfully"}
    except Exception as e:
        print("Exception:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or error deleting variant type",
        )

@router.get("/products/{productId}/variants", response_model=List[VariantResponse])
async def get_variants_by_product(productId: int):
    try:
        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM ProductVariants WHERE productId=?", (productId,))
        variants = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "variantId": variant[0],
                "productId": variant[1],
                "variantType": variant[2],
                "variantValue": variant[3],
                "stock": variant[4],
                "price": variant[5]
            }
            for variant in variants
        ]
    except Exception as e:
        print("Exception:", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching variants by product",
        )

@router.post("/products/{productId}/variants", response_model=VariantResponse)
async def create_product_variant(
    productId: int, variant: ProductVariantCreate, token: str = Depends(oauth2_scheme)
):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
            )

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO ProductVariants (productId, variantType, variantValue, stock, price)
            VALUES (?, ?, ?, ?, ?)
        """,
            (productId, variant.variantType, variant.variantValue, variant.stock, variant.price),
        )
        conn.commit()

        cursor.execute("SELECT * FROM ProductVariants WHERE variantId=@@IDENTITY")
        new_variant = cursor.fetchone()

        cursor.close()
        conn.close()

        if not new_variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product Variant creation failed"
            )

        return {
            "variantId": new_variant[0],
            "productId": new_variant[1],
            "variantType": new_variant[2],
            "variantValue": new_variant[3],
            "stock": new_variant[4],
            "price": new_variant[5]
        }
    except Exception as e:
        print("Exception:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or error creating product variant",
        )

@router.put("/products/{productId}/variants/{variantId}", response_model=VariantResponse)
async def update_product_variant(
    productId: int, variantId: int, variant: ProductVariantUpdate, token: str = Depends(oauth2_scheme)
):
    try:
        payload = verify_token(token)
        username = payload.get("sub")
        
        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE ProductVariants
            SET variantType=?, variantValue=?, stock=?, price=?
            WHERE variantId=? AND productId=?
            """,
            (variant.variantType, variant.variantValue, variant.stock, variant.price, variantId, productId),
        )
        conn.commit()

        cursor.execute("SELECT * FROM ProductVariants WHERE variantId=? AND productId=?", (variantId, productId))
        updated_variant = cursor.fetchone()

        cursor.close()
        conn.close()

        if not updated_variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product Variant not found"
            )

        return {
            "variantId": updated_variant[0],
            "productId": updated_variant[1],
            "variantType": updated_variant[2],
            "variantValue": updated_variant[3],
            "stock": updated_variant[4],
            "price": updated_variant[5]
        }
    except Exception as e:
        print("Exception:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or error updating product variant",
        )

@router.delete("/products/{productId}/variants/{variantId}")
async def delete_product_variant(
    productId: int, variantId: int, token: str = Depends(oauth2_scheme)
):
    try:
        payload = verify_token(token)
        username = payload.get("sub")
        
        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM ProductVariants WHERE variantId=? AND productId=?", (variantId, productId))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Product Variant not found"
            )

        cursor.close()
        conn.close()

        return {"detail": "Product Variant deleted successfully"}
    except Exception as e:
        print("Exception:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or error deleting product variant",
        )
