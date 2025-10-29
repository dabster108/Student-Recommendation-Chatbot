from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models.user import User
from ..schemas.user import UserCreate, UserResponse, Token, PasswordResetRequest, PasswordReset
from ..core.database import get_db
from ..core.security import get_password_hash, verify_password, create_access_token, verify_token
from ..utils.email import send_verification_email, send_password_reset_email
from ..core.config import settings

router = APIRouter(tags=["Authentication"])

@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter((User.email == user.email) | (User.username == user.username)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email or username already registered")
    
    # Create user
    hashed_password = get_password_hash(user.password)
    verification_token = create_access_token({"sub": user.email})
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        verification_token=verification_token
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send verification email
    await send_verification_email(user.email, verification_token)
    
    return db_user

@router.post("/login", response_model=Token)
async def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified",
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        return {"message": "Email already verified"}
    
    user.is_verified = True
    user.verification_token = None
    db.commit()
    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        return {"message": "Email already verified"}
    
    new_token = create_access_token({"sub": user.email})
    user.verification_token = new_token
    db.commit()
    await send_verification_email(user.email, new_token)
    return {"message": "Verification email resent"}

@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if user:
        reset_token = create_access_token({"sub": user.email})
        user.reset_token = reset_token
        db.commit()
        await send_password_reset_email(user.email, reset_token)
    return {"message": "If email exists, password reset link has been sent"}

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    payload = verify_token(reset_data.token)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user or user.reset_token != reset_data.token:
        raise HTTPException(status_code=400, detail="Invalid token")
    
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.reset_token = None
    db.commit()
    return {"message": "Password reset successfully"}