from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.auth import UserCreate, UserLogin, Token
from app.services.auth_service import create_user, authenticate_user
from app.database import get_db  # Assuming you have a get_db function to get DB session

router = APIRouter()

# Signup endpoint (Create new user)
@router.post("/signup", response_model=Token)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    try:
        new_user = create_user(db=db, user=user)
        token = authenticate_user(db=db, user=UserLogin(username=user.username, password=user.password))
        return token
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Login endpoint (Generate JWT token for existing user)
@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    try:
        token = authenticate_user(db=db, user=user)
        return token
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
