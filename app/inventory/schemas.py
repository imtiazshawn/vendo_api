from pydantic import BaseModel

class InventoryResponse(BaseModel):
    inventory_id: int
    product_id: int
    quantity: int
    created_at: str
    updated_at: str

class InventoryUpdate(BaseModel):
    quantity: int

class InitialInventory(BaseModel):
    product_id: int
    quantity: int