from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Route
from app.schemas import DepartureRequest
from app.services.eta_service import predict_arrival, recommend_departure


router = APIRouter(prefix="/api/departure", tags=["Departure"])


@router.get("/")
def smart_departure(
    required_arrival: str = "09:00",
    travel_minutes: float = 24,
    predicted_delay: float = 6,
    safety_buffer: int = 10,
):
    return recommend_departure(
        required_arrival,
        travel_minutes,
        predicted_delay,
        safety_buffer,
    )


@router.post("/")
def smart_departure_post(payload: DepartureRequest, db: Session = Depends(get_db)):
    route = (
        db.query(Route)
        .filter(Route.route_number == payload.route_number)
        .first()
    )
    eta = predict_arrival(
        speed_kmh=26,
        distance_km=route.distance_km if route else 2.8,
        occupancy=0.55,
        traffic_level=0.45,
    )
    return {
        "origin": payload.origin,
        "destination": payload.destination,
        "route_number": payload.route_number,
        **recommend_departure(
            payload.required_arrival,
            eta["travel_time_minutes"],
            eta["predicted_delay_minutes"],
            payload.safety_buffer,
        ),
    }
