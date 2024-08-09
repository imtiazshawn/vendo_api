from pydantic import BaseModel

class PaymentCreate(BaseModel):
    order_id: int
    amount: float
    payment_method: str
    payment_status: str

class PaymentResponse(BaseModel):
    payment_id: int
    order_id: int
    amount: float
    payment_method: str
    payment_status: str
    created_at: str
    updated_at: str