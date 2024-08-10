from pydantic import BaseModel

class SupportTicketCreate(BaseModel):
    subject: str
    message: str

class SupportTicketUpdate(BaseModel):
    subject: str
    message: str
    status: str

class SupportTicketResponse(BaseModel):
    ticket_id: int
    user_id: int
    subject: str
    message: str
    status: str
    created_at: str
    updated_at: str
