from pydantic import BaseModel

class UserInput(BaseModel):
    role: str
    message: str
