from fastapi import FastAPI
from app.core.database import engine, Base  # Updated import path
from app.routers import auth, users        # Updated import path
import asyncio

app = FastAPI()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(auth.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "Authentication Service"}