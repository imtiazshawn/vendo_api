from pydantic import BaseModel

class VariantTypeCreate(BaseModel):
    categoryId: int
    variantType: str

class VariantTypeUpdate(BaseModel):
    variantType: str

class VariantResponse(BaseModel):
    variantTypeId: int
    categoryId: int
    variantType: str

class ProductVariantCreate(BaseModel):
    variantType: str
    variantValue: str
    stock: int
    price: float

class ProductVariantUpdate(BaseModel):
    variantType: str
    variantValue: str
    stock: int
    price: float

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    category_id: int
    image_url: str
    created_at: str
    updated_at: str
