from fastapi import APIRouter, HTTPException, status
from app.auth.schemas import UserCreate, UserResponse
from app.auth.services import get_password_hash
from app.services.dbServices import connect_to_database
from datetime import datetime
from typing import List

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
async def get_all_users():
    conn = await connect_to_database()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users")
    db_users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not db_users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found")
    
    users = []
    for user in db_users:
        try:
            user_data = {
                "id": user[0],
                "email": user[1],
                "username": user[2],
                "full_name": user[3],
                "phone": user[4],
                "address": user[5]
            }
            users.append(user_data)
        except Exception as e:  # Catch all exceptions
            print(f"Invalid data found: {user}, Error: {e}")
            continue
    
    return users

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    conn = await connect_to_database()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email=?", (user.email,))
    db_user = cursor.fetchone()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    created_at = datetime.now()
    updated_at = datetime.now()

    cursor.execute(
        """
        INSERT INTO users (email, username, passwordHash, fullName, phone, address, createdAt, updatedAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, 
        (user.email, user.username, hashed_password, user.full_name, user.phone, user.address, created_at, updated_at)
    )
    conn.commit()
    
    cursor.execute("SELECT * FROM users WHERE email=?", (user.email,))
    db_user = cursor.fetchone()
    
    cursor.close()
    conn.close()

    # Log the data retrieved
    print(f"Retrieved user data: {db_user}")
    
    return {
        "id": db_user[0],
        "email": db_user[1],
        "username": db_user[2],
        "full_name": db_user[3],
        "phone": db_user[4],
        "address": db_user[5]
    }
