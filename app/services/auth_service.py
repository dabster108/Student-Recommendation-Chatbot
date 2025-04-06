from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, Token
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import SECRET_KEY
from datetime import timedelta

# Create a new user
def create_user(db: Session, user: UserCreate):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise Exception("Username already registered")
    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Authenticate user (login)
def authenticate_user(db: Session, user: UserLogin):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise Exception("Invalid username or password")
    
    access_token = create_access_token(
        data={"sub": db_user.username},
        expires_delta=timedelta(hours=1)  # Token expiration time of 1 hour
    )
    
    return Token(access_token=access_token, token_type="bearer")
