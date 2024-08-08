from pydantic import BaseModel
from typing import Optional

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    category_id: int
    image_url: str
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True
