from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Route, StopTime
from app.services.eta_service import predict_arrival
from app.services.transit import compare_routes, tracking_payload


router = APIRouter(prefix="/api/routes", tags=["Routes"])


@router.get("/search")
def search_routes(from_stop: str, to_stop: str, db: Session = Depends(get_db)):
    return compare_routes(db, from_stop, to_stop)


@router.get("/compare")
def compare(from_stop: str, to_stop: str, db: Session = Depends(get_db)):
    return {"from_stop": from_stop, "to_stop": to_stop, "routes": compare_routes(db, from_stop, to_stop)}


@router.get("/{route_number}/tracking")
def route_tracking(route_number: str, db: Session = Depends(get_db)):
    return tracking_payload(db, route_number)


@router.get("/{route_number}/eta")
def route_eta(route_number: str, stop_name: str, db: Session = Depends(get_db)):
    route = db.query(Route).filter(Route.route_number == route_number).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    stop_time = (
        db.query(StopTime)
        .filter(StopTime.route_id == route.id)
        .order_by(StopTime.scheduled_arrival.desc())
        .first()
    )
    result = predict_arrival(
        speed_kmh=(stop_time.speed_kmh if stop_time else 25) or 25,
        distance_km=(stop_time.distance_from_previous if stop_time else route.distance_km) or 2,
        occupancy=(stop_time.occupancy if stop_time else 0.5) or 0.5,
        traffic_level=(stop_time.traffic_level if stop_time else 0.5) or 0.5,
    )
    return {"route_number": route_number, "stop_name": stop_name, **result}
