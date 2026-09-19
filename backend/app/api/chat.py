from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services.transit import chat_reply


router = APIRouter(prefix="/api/chat", tags=["AI Assistant"])


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    return {"reply": chat_reply(db, request.message)}
