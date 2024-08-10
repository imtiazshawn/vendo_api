from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer

from app.auth.token import verify_token
from app.services.dbServices import connect_to_database
from app.utils.is_admin import is_admin
from app.notifications.schemas import NotificationResponse, NotificationCreate, NotificationUpdate
from app.utils.date_convert import format_datetime

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/admin/auth/login")

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT userId FROM Users WHERE username=?", (username,))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user_id = user[0]

        cursor.execute("SELECT * FROM Notifications WHERE userId=?", (user_id,))
        notifications = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "notification_id": item[0],
                "user_id": item[1],
                "message": item[2],
                "is_read": item[3],
                "created_at": format_datetime(item[4]),
                "updated_at": format_datetime(item[5]),
            }
            for item in notifications
        ]
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching notifications")

@router.post("/admin/notifications", response_model=NotificationResponse)
async def create_notification(notification_create: NotificationCreate, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO Notifications (userId, message, isRead, createdAt, updatedAt)
            VALUES ((SELECT userId FROM Users WHERE username=?), ?, ?, GETDATE(), GETDATE())
            """,
            (username, notification_create.message, False),
        )
        conn.commit()

        cursor.execute("SELECT * FROM Notifications WHERE notificationId=@@IDENTITY")
        new_notification = cursor.fetchone()

        cursor.close()
        conn.close()

        if not new_notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to create notification")

        return {
            "notification_id": new_notification[0],
            "user_id": new_notification[1],
            "message": new_notification[2],
            "is_read": new_notification[3],
            "created_at": format_datetime(new_notification[4]),
            "updated_at": format_datetime(new_notification[5]),
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error creating notification")

@router.delete("/notifications/{notification_id}", response_model=NotificationResponse)
async def delete_notification(notification_id: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Notifications WHERE notificationId=?", (notification_id,))
        notification = cursor.fetchone()

        if not notification:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

        cursor.execute("DELETE FROM Notifications WHERE notificationId=?", (notification_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return {
            "notification_id": notification[0],
            "user_id": notification[1],
            "message": notification[2],
            "is_read": notification[3],
            "created_at": format_datetime(notification[4]),
            "updated_at": format_datetime(notification[5]),
        }
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error deleting notification")
