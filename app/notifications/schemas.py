from pydantic import BaseModel
from datetime import datetime

class NotificationBase(BaseModel):
    message: str

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    notification_id: int
    user_id: int
    is_read: bool
    created_at: datetime
    updated_at: datetime

class NotificationUpdate(BaseModel):
    is_read: bool
