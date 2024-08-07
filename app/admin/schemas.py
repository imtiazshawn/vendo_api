from pydantic import BaseModel, EmailStr
from typing import Optional

class AdminUserResponse(BaseModel):
    id: int
    email: EmailStr
    username: str
    full_name: str

class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
