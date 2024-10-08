from fastapi import APIRouter, HTTPException, status, Depends
from app.auth.admin_schemas import AdminLoginRequest, AdminTokenResponse
from app.auth.services import verify_password
from app.services.dbServices import connect_to_database
from app.auth.token import create_access_token, create_refresh_token, verify_token
from fastapi.security import OAuth2PasswordBearer
from app.utils.is_admin import is_admin

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/admin/auth/login")

router = APIRouter()

@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(login_request: AdminLoginRequest):
    conn = await connect_to_database()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Admins WHERE email=?", (login_request.email,))
    db_admin = cursor.fetchone()

    cursor.close()
    conn.close()

    if not db_admin or not verify_password(login_request.password, db_admin[3]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": db_admin[1]})
    refresh_token = create_refresh_token(data={"sub": db_admin[1]})

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/logout", status_code=status.HTTP_200_OK)
async def admin_logout(token: str = Depends(oauth2_scheme)):
    try:
        verify_token(token)
        return {"message": "Successfully logged out"}
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.get("/verify-token")
async def verify_and_check_admin(token: str = Depends(oauth2_scheme)):
    try:
        # Verify the token
        payload = verify_token(token)
        username = payload['sub']

        # Check if the user is an admin
        if not await is_admin(username):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        return {"valid": True, "payload": payload}

    except HTTPException as e:
        # Handle known HTTP exceptions
        raise e
    except Exception as e:
        # Handle unexpected exceptions
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token or error checking admin status")