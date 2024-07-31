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

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"