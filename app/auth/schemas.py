from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    full_name: str
    phone: str
    address: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    phone: str
    address: str
