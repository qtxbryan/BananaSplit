import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from src.auth.schemas import UserCreate, UserLogin, PasswordResetConfirm, PasswordResetRequest
from src.auth.utils import get_password_hash, verify_password, create_access_token, send_reset_email
from src.auth.database import get_user_by_email_or_username, create_user, update_user_password, is_token_blacklisted, blacklist_token

from src.group.service import GroupService

ROUTE_PREFIX = "/" + os.getenv("EXPENSE_SERVICE_VERSION") + "/auth"
router = APIRouter(prefix=ROUTE_PREFIX, tags=["auth-service"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

group_service = GroupService()

@router.post("/register")
async def register(user: UserCreate):
    db_user = await get_user_by_email_or_username(user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email or username already registered")
    hashed_password = get_password_hash(user.password)
    user_id = await create_user(user.email, user.phone_number, user.username, user.pic_url, hashed_password)
    if user.pending_user_id is not None:
        await group_service.add_user_to_group(user.pending_user_id, user_id)
    return {"message": "User registered successfully", "user_id": str(user_id)}


@router.post("/login")
async def login(user: UserLogin):
    db_user = await get_user_by_email_or_username(user.email)
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    access_token = create_access_token({"sub": db_user["email"]})
    if user.pending_user_id is not None:
        await group_service.add_user_to_group(user.pending_user_id, str(db_user["_id"]))

    return {"access_token": access_token, "token_type": "bearer", "user_id": str(db_user["_id"])}


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None or is_token_blacklisted(token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or blacklisted token")
        
        # Blacklist the token
        await blacklist_token(token)
        return {"message": "Logged out successfully"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@router.post("/forgetpassword")
async def forgetpassword(request: PasswordResetRequest):
    user = await get_user_by_email_or_username(request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    reset_token = create_access_token({"sub": user["email"]})
    await send_reset_email(user["_id"], reset_token)
    return {"message": "Password reset email sent"}

@router.post("/resetpassword")
async def resetpassword(confirm: PasswordResetConfirm):
    try:
        payload = jwt.decode(confirm.token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None or email != confirm.email:
            raise HTTPException(status_code=400, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    hashed_password = get_password_hash(confirm.new_password)
    await update_user_password(confirm.email, hashed_password)
    return {"message": "Password successfully changed"}
