from pydantic import BaseModel
from typing import Optional

class UserInput(BaseModel):
    id: Optional[str]
    text: str

class CategorizedResponse(BaseModel):
    text: str
    category: str
    remarks: str
    description: str

class RawTextInput(BaseModel):
    raw_text: str
