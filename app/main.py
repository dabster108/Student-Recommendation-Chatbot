from fastapi import FastAPI
from app.api.v1.endpoints.chat import router as chat_router

app = FastAPI()

app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])
