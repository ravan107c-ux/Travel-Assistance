from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Bus, Route
from app.services.transit import tracking_payload


router = APIRouter(prefix="/api/buses", tags=["Buses"])


@router.get("/")
def get_buses(db: Session = Depends(get_db)):
    buses = db.query(Bus).filter(Bus.active.is_(True)).all()
    return [
        {
            "bus_number": bus.bus_number,
            "route_id": bus.route_id,
            "capacity": bus.capacity,
            "speed_kmh": bus.speed_kmh,
            "occupancy": bus.occupancy,
            "status": bus.status,
        }
        for bus in buses
    ]


@router.get("/track/{route_number}")
def track_route(route_number: str, db: Session = Depends(get_db)):
    return tracking_payload(db, route_number)


@router.get("/{bus_number}")
def get_bus(bus_number: str, db: Session = Depends(get_db)):
    bus = db.query(Bus).filter(Bus.bus_number == bus_number).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    route = db.query(Route).filter(Route.id == bus.route_id).first()
    return {
        "bus_number": bus.bus_number,
        "route_id": bus.route_id,
        "route_number": route.route_number if route else None,
        "capacity": bus.capacity,
        "active": bus.active,
        "speed_kmh": bus.speed_kmh,
        "occupancy": bus.occupancy,
        "status": bus.status,
        "latitude": bus.latitude,
        "longitude": bus.longitude,
    }
