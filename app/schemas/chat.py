from pydantic import BaseModel

class UserInput(BaseModel):
    message: str
    role: str = "user"
    conversation_id: str
