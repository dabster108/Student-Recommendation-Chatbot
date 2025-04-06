from pydantic import BaseModel
from typing import Union

class UserInput(BaseModel):
    message: Union[str, int]  # Allows both string and integer inputs
    role: str = "user"
    conversation_id: str


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
