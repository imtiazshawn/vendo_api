from pydantic import BaseModel
from typing import List
from datetime import datetime

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderCreate(BaseModel):
    total_amount: float
    items: List[OrderItemCreate]

class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderResponse(BaseModel):
    order_id: int
    user_id: int
    total_amount: float
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

class OrderStatusUpdate(BaseModel):
    status: str

