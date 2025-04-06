from fastapi import APIRouter, HTTPException
from app.schemas.chat import UserInput, ChatResponse
from app.services.groq_service import GroqService

router = APIRouter()

@router.post("/chat/", response_model=ChatResponse)
async def chat(input: UserInput):
    groq_service = GroqService()
    try:
        response = groq_service.get_response(input)
        return ChatResponse(
            response=response,
            conversation_id=input.conversation_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
