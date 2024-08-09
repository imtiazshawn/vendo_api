from pydantic import BaseModel

class CartItemResponse(BaseModel):
    cart_item_id: int
    product_id: int
    quantity: int
    created_at: str
    updated_at: str

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int