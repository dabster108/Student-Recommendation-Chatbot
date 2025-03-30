from pydantic import BaseModel
from typing import Union

class UserInput(BaseModel):
    message: Union[str, int]  # Allows both string and integer inputs
    role: str = "user"
    conversation_id: str


'''
{
  "message": "Find the best books",
  "role": "user",
  "conversation_id": "12345"
}
'''