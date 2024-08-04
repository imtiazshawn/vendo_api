from pydantic import BaseModel

class AdminLoginRequest(BaseModel):
    email: str
    password: str

class AdminTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
