from pydantic import BaseModel

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

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    category_id: int
    image_url: str

class ProductUpdate(BaseModel):
    name: str
    description: str
    price: float
    category_id: int
    image_url: str

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    category_id: int
    image_url: str
    created_at: str
    updated_at: str