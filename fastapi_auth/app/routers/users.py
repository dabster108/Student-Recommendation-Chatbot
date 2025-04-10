from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.user import UserResponse
from ..core.database import get_db
from ..dependencies.security import get_current_user

router = APIRouter(tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user