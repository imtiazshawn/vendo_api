from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

from app.auth.token import verify_token
from app.services.dbServices import connect_to_database
from app.user.schemas import UserProfileUpdate, UserResponse
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def is_admin(payload):
    return payload.get("role") == "admin"

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        if not is_admin(payload):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "id": user[0],
                "email": user[1],
                "username": user[2],
                "full_name": user[3],
                "phone": user[4],
                "address": user[5]
            }
            for user in users
        ]
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or error fetching users")

@router.get("/users/{userId}", response_model=UserResponse)
async def get_user_details(userId: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        if not is_admin(payload):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE userId=?", (userId,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return {
            "id": user[0],
            "email": user[1],
            "username": user[2],
            "full_name": user[3],
            "phone": user[4],
            "address": user[5]
        }
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or error fetching user details")

@router.put("/users/{userId}", response_model=UserResponse)
async def update_user(userId: int, profile_update: UserProfileUpdate, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        if not is_admin(payload):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE userId=?", (userId,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        update_fields = []
        params = []
        if profile_update.email:
            update_fields.append("email=?")
            params.append(profile_update.email)
        if profile_update.username:
            update_fields.append("username=?")
            params.append(profile_update.username)
        if profile_update.full_name:
            update_fields.append("fullName=?")
            params.append(profile_update.full_name)
        if profile_update.phone:
            update_fields.append("phone=?")
            params.append(profile_update.phone)
        if profile_update.address:
            update_fields.append("address=?")
            params.append(profile_update.address)

        if not update_fields:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

        update_fields.append("updatedAt=GETDATE()")
        params.append(userId)

        update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE userId=?"
        cursor.execute(update_query, tuple(params))
        conn.commit()

        cursor.execute("SELECT * FROM users WHERE userId=?", (userId,))
        updated_user = cursor.fetchone()

        cursor.close()
        conn.close()

        return {
            "id": updated_user[0],
            "email": updated_user[1],
            "username": updated_user[2],
            "full_name": updated_user[3],
            "phone": updated_user[4],
            "address": updated_user[5]
        }
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or error updating user")

@router.delete("/users/{userId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(userId: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        if not is_admin(payload):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE userId=?", (userId,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        cursor.execute("DELETE FROM users WHERE userId=?", (userId,))
        conn.commit()

        cursor.close()
        conn.close()

    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or error deleting user")
