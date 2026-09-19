from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.transit import crowd_payload


router = APIRouter(prefix="/api/crowd", tags=["Crowd"])


@router.get("/{route_number}")
def crowd_forecast(route_number: str, db: Session = Depends(get_db)):
    return crowd_payload(db, route_number)
