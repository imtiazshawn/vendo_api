from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from app.auth.token import verify_token
from app.services.dbServices import connect_to_database
from app.utils.is_admin import is_admin
from app.reviews.schemas import ReviewCreate, ReviewResponse, ReviewUpdate
from app.utils.date_convert import format_datetime

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/admin/auth/login")


@router.post("/products/{product_id}/reviews", response_model=ReviewResponse)
async def add_review(
    product_id: int, review: ReviewCreate, token: str = Depends(oauth2_scheme)
):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT userId FROM Users WHERE username=?", (username,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user_id = user[0]

        cursor.execute(
            "SELECT 1 FROM Reviews WHERE productId=? AND userId=?", (product_id, user_id)
        )
        existing_review = cursor.fetchone()

        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User has already reviewed this product"
            )

        cursor.execute(
            """
            INSERT INTO Reviews (productId, userId, rating, comment, createdAt, updatedAt)
            VALUES (?, ?, ?, ?, GETDATE(), GETDATE())
        """,
            (product_id, user_id, review.rating, review.comment),
        )
        conn.commit()

        cursor.execute("SELECT * FROM Reviews WHERE reviewId=@@IDENTITY")
        new_review = cursor.fetchone()

        if not new_review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Failed to create review"
            )

        review_response = {
            "review_id": new_review[0],
            "product_id": new_review[1],
            "user_id": new_review[2],
            "rating": new_review[3],
            "comment": new_review[4],
            "created_at": format_datetime(new_review[5]),
            "updated_at": format_datetime(new_review[6]),
        }

        cursor.close()
        conn.close()

        return review_response
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding review",
        )


@router.get("/products/{product_id}/reviews", response_model=List[ReviewResponse])
async def get_reviews(product_id: int):
    try:
        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Reviews WHERE productId=?", (product_id,))
        reviews = cursor.fetchall()

        if not reviews:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No reviews found"
            )

        review_list = [
            {
                "review_id": review[0],
                "product_id": review[1],
                "user_id": review[2],
                "rating": review[3],
                "comment": review[4],
                "created_at": format_datetime(review[5]),
                "updated_at": format_datetime(review[6]),
            }
            for review in reviews
        ]

        cursor.close()
        conn.close()

        return review_list
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching reviews",
        )


@router.put("/products/{product_id}/reviews/{review_id}", response_model=ReviewResponse)
async def update_review(
    product_id: int,
    review_id: int,
    review: ReviewUpdate,
    token: str = Depends(oauth2_scheme),
):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT userId FROM Users WHERE username=?", (username,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user_id = user[0]

        cursor.execute(
            "SELECT * FROM Reviews WHERE reviewId=? AND userId=?", (review_id, user_id)
        )
        existing_review = cursor.fetchone()

        if not existing_review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found or not authorized",
            )

        cursor.execute(
            """
            UPDATE Reviews
            SET rating = ?, comment = ?, updatedAt = GETDATE()
            WHERE reviewId = ?
        """,
            (review.rating, review.comment, review_id),
        )
        conn.commit()

        cursor.execute("SELECT * FROM Reviews WHERE reviewId=?", (review_id,))
        updated_review = cursor.fetchone()

        if not updated_review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Failed to update review"
            )

        review_response = {
            "review_id": updated_review[0],
            "product_id": updated_review[1],
            "user_id": updated_review[2],
            "rating": updated_review[3],
            "comment": updated_review[4],
            "created_at": format_datetime(updated_review[5]),
            "updated_at": format_datetime(updated_review[6]),
        }

        cursor.close()
        conn.close()

        return review_response
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating review",
        )


@router.delete(
    "/products/{product_id}/reviews/{review_id}", status_code=status.HTTP_200_OK
)
async def delete_review(
    product_id: int, review_id: int, token: str = Depends(oauth2_scheme)
):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT userId FROM Users WHERE username=?", (username,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user_id = user[0]

        cursor.execute(
            "SELECT * FROM Reviews WHERE reviewId=? AND userId=?", (review_id, user_id)
        )
        existing_review = cursor.fetchone()

        if not existing_review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found or not authorized",
            )

        cursor.execute("DELETE FROM Reviews WHERE reviewId=?", (review_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return {"detail": "Review successfully deleted"}
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting review",
        )
