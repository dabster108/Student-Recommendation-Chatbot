from pydantic import BaseModel
from typing import Optional

# Schema for signup request
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

# Schema for login request
class UserLogin(BaseModel):
    username: str
    password: str

# Schema for JWT token response
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for User Response
class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True
