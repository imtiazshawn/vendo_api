from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from typing import List

from app.auth.schemas import UserCreate, UserResponse, LoginRequest, TokenResponse
from app.auth.services import get_password_hash, verify_password
from app.services.dbServices import connect_to_database
from app.auth.token import create_access_token, create_refresh_token, verify_token

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


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
        except Exception as e:
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

    print(f"Retrieved user data: {db_user}")
    
    return {
        "id": db_user[0],
        "email": db_user[1],
        "username": db_user[2],
        "full_name": db_user[3],
        "phone": db_user[4],
        "address": db_user[5]
    }

@router.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest):
    conn = await connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email=?", (login_request.email,))
    db_user = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if not db_user or not verify_password(login_request.password, db_user[3]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Generate tokens
    access_token = create_access_token(data={"sub": db_user[1]})
    refresh_token = create_refresh_token(data={"sub": db_user[1]})

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(token: str = Depends(oauth2_scheme)):
    try:
        verify_token(token)
        return {"message": "Successfully logged out"}
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    try:
        # Verify the refresh token
        payload = verify_token(refresh_token)
        email = payload.get("sub")
        
        # Generate new tokens
        access_token = create_access_token(data={"sub": email})
        new_refresh_token = create_refresh_token(data={"sub": email})

        return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
