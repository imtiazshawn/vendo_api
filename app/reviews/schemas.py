from pydantic import BaseModel

class ReviewCreate(BaseModel):
    rating: int
    comment: str

class ReviewUpdate(BaseModel):
    rating: int
    comment: str

class ReviewResponse(BaseModel):
    review_id: int
    product_id: int
    user_id: int
    rating: int
    comment: str
    created_at: str
    updated_at: str