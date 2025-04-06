from fastapi import APIRouter
from app.schemas.chat import UserInput
from app.services.groq_service import GroqService

router = APIRouter()

groq_service = GroqService()

@router.post("/response")
async def get_chat_response(user_input: UserInput):
    try:
        response = groq_service.get_response(user_input)
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}
