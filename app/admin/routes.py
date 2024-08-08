from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.auth.token import verify_token
from app.auth.services import get_password_hash
from app.services.dbServices import connect_to_database
from app.admin.schemas import AdminUserResponse, AdminUserUpdate, AdminCreate
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/admin/auth/login")

async def is_admin(username: str) -> bool:
    conn = await connect_to_database()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM Admins WHERE username=?", (username,))
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists

@router.get("/admins", response_model=List[AdminUserResponse])
async def get_all_users(token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload['sub']
        
        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Admins")
        admins = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            {
                "id": admin[0],
                "username": admin[1],
                "email": admin[2],
                "full_name": admin[4]
            }
            for admin in admins
        ]
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or error fetching admins")

@router.get("/admins/{userId}")
async def get_user_details(userId: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload['sub']
        
        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        print(f"Querying for userId: {userId}")
        cursor.execute(f"SELECT * FROM Admins WHERE adminId={userId}")
        admin = cursor.fetchone()

        print(f"Query result: {admin}")
        cursor.close()
        conn.close()

        if not admin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return {
            "id": admin[0],
            "username": admin[1],
            "email": admin[2],
            "full_name": admin[4]
        }
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or error fetching user details")
    

@router.post("/admins", response_model=AdminUserResponse)
async def create_admin(admin_create: AdminCreate, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload['sub']
        
        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        hashed_password = get_password_hash(admin_create.password)

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO Admins (username, email, passwordHash, fullName, createdAt, updatedAt) "
            "VALUES (?, ?, ?, ?, GETDATE(), GETDATE())",
            (admin_create.username, admin_create.email, hashed_password, admin_create.full_name)
        )
        conn.commit()

        cursor.execute("SELECT * FROM Admins WHERE username=?", (admin_create.username,))
        new_admin = cursor.fetchone()

        cursor.close()
        conn.close()

        if not new_admin:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create admin")

        return {
            "id": new_admin[0],
            "username": new_admin[1],
            "email": new_admin[2],
            "full_name": new_admin[4]
        }
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or error creating admin")


@router.put("/admins/{userId}", response_model=AdminUserResponse)
async def update_user(userId: int, user_update: AdminUserUpdate, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload['sub']
        
        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Admins WHERE adminId=?", (userId,))
        admin = cursor.fetchone()

        if not admin:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        update_fields = []
        params = []
        if user_update.email:
            update_fields.append("email=?")
            params.append(user_update.email)
        if user_update.username:
            update_fields.append("username=?")
            params.append(user_update.username)
        if user_update.full_name:
            update_fields.append("fullName=?")
            params.append(user_update.full_name)

        if not update_fields:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

        update_fields.append("updatedAt=CURRENT_TIMESTAMP")
        params.append(userId)

        update_query = f"UPDATE Admins SET {', '.join(update_fields)} WHERE adminId=?"
        cursor.execute(update_query, tuple(params))
        conn.commit()

        cursor.execute("SELECT * FROM Admins WHERE adminId=?", (userId,))
        updated_admin = cursor.fetchone()

        cursor.close()
        conn.close()

        return {
            "id": updated_admin[0],
            "username": updated_admin[1],
            "email": updated_admin[2],
            "full_name": updated_admin[4]
        }
    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or error updating user")


@router.delete("/admins/{userId}", status_code=status.HTTP_200_OK)
async def delete_user(userId: int, token: str = Depends(oauth2_scheme)):
    try:
        payload = verify_token(token)
        username = payload['sub']
        
        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        conn = await connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Admins WHERE adminId=?", (userId,))
        admin = cursor.fetchone()

        if not admin:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        cursor.execute("DELETE FROM Admins WHERE adminId=?", (userId,))
        conn.commit()

        cursor.close()
        conn.close()

        return {"message": f"User with ID {userId} has been successfully deleted."}

    except Exception as e:
        print('Exception:', e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or error deleting user")
