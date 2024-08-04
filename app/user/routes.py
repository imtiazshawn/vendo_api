from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from app.auth.token import verify_token
from app.auth.schemas import UserResponse
from app.services.dbServices import connect_to_database
from app.user.schemas import UserProfileUpdate

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")
        print('username:', username)

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        db_user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user = {
            "id": db_user[0],
            "email": db_user[1],
            "username": db_user[2],
            "full_name": db_user[3],
            "phone": db_user[4],
            "address": db_user[5]
        }
        print('User:', user)
        return user
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(profile_update: UserProfileUpdate, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload.get("sub")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        db_user = cursor.fetchone()

        if not db_user:
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
        params.append(username)

        update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE username=?"
        cursor.execute(update_query, tuple(params))
        conn.commit()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        updated_user = cursor.fetchone()

        cursor.close()
        conn.close()

        return {
            "id": updated_user[0],
            "username": updated_user[1],
            "email": updated_user[2],
            "full_name": updated_user[4],
            "phone": updated_user[5],
            "address": updated_user[6]
        }
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
