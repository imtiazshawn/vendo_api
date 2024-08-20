from pydantic import BaseModel
from datetime import datetime

class SalesReport(BaseModel):
    product_id: int
    product_name: str
    total_sales: float

class OrderReport(BaseModel):
    order_id: int
    user_id: int
    total_amount: float
    order_date: datetime

class UserActivityReport(BaseModel):
    user_id: int
    username: str
    total_orders: int
    total_amount_spent: float

class DateRange(BaseModel):
    year: int
    month: int