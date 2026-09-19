from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.ml.predictor import models
from app.models import Alert, Bus, Route, Stop, StopTime
from app.services.eta_service import predict_arrival, recommend_departure


def crowd_band(occupancy: float) -> str:
    return models.crowd_label(occupancy)


def comfort_score(travel_minutes: float, occupancy: float, transfers: int) -> int:
    score = 100
    score -= max(0, travel_minutes - 18) * 1.2
    score -= occupancy * 28
    score -= transfers * 12
    return int(max(55, min(98, round(score))))


def seed_database(db: Session) -> None:
    if db.query(Route).count() > 0:
        return

    stops = [
        Stop(stop_name="Town Hall", latitude=9.9195, longitude=78.1194),
        Stop(stop_name="Anna Nagar", latitude=9.9288, longitude=78.1412),
        Stop(stop_name="KK Nagar", latitude=9.9396, longitude=78.1478),
        Stop(stop_name="Arappalayam", latitude=9.9390, longitude=78.1036),
        Stop(stop_name="Mattuthavani", latitude=9.9442, longitude=78.1558),
        Stop(stop_name="Periyar", latitude=9.9198, longitude=78.1146),
        Stop(stop_name="Madurai Junction", latitude=9.9200, longitude=78.1103),
        Stop(stop_name="Anna Nagar College", latitude=9.9312, longitude=78.1433),
    ]
    db.add_all(stops)
    db.flush()

    routes = [
        Route(
            route_number="21B",
            route_name="Town Hall → Mattuthavani",
            origin="Town Hall",
            destination="Mattuthavani",
            distance_km=2.8,
            stop_count=7,
            transfers=0,
        ),
        Route(
            route_number="11",
            route_name="Periyar → Anna Nagar",
            origin="Periyar",
            destination="Anna Nagar",
            distance_km=1.9,
            stop_count=5,
            transfers=0,
        ),
        Route(
            route_number="4A",
            route_name="Madurai Junction → K.K. Nagar",
            origin="Madurai Junction",
            destination="K.K. Nagar",
            distance_km=4.6,
            stop_count=9,
            transfers=0,
        ),
        Route(
            route_number="11+4A",
            route_name="Town Hall → Mattuthavani via transfer",
            origin="Town Hall",
            destination="Mattuthavani",
            distance_km=3.4,
            stop_count=8,
            transfers=1,
        ),
    ]
    db.add_all(routes)
    db.flush()

    route_by_number = {route.route_number: route for route in routes}
    now = datetime.now()
    buses = []
    for index in range(1, 19):
        route = routes[index % len(routes[:3])]
        occupancy = models.predict_occupancy(now.hour)
        buses.append(
            Bus(
                bus_number=f"{route.route_number}-{100 + index}",
                route_id=route.id,
                capacity=52,
                active=True,
                speed_kmh=22 + (index % 12),
                occupancy=round(occupancy + (index % 5) * 0.03, 2),
                latitude=9.92 + index * 0.001,
                longitude=78.12 + index * 0.001,
                progress=0.35 + (index % 6) * 0.08,
                status="ON TIME" if index % 4 else "DELAYED",
            )
        )
    db.add_all(buses)
    db.flush()

    stop_lookup = {stop.stop_name: stop for stop in stops}
    history = []
    for day_offset in range(5):
        service_date = (now - timedelta(days=day_offset)).date()
        weekday = (now - timedelta(days=day_offset)).weekday()
        for hour in (7, 9, 11, 13, 15, 17, 18, 19, 21):
            for route in routes[:3]:
                occupancy = models.predict_occupancy(hour, weekday)
                traffic = 0.25 + (0.45 if hour in (8, 9, 17, 18, 19) else 0.1)
                delay = models.predict_delay(
                    hour=hour,
                    minute=0,
                    day_of_week=weekday,
                    speed_kmh=26,
                    occupancy=occupancy,
                    traffic_level=traffic,
                    distance_from_previous=route.distance_km,
                )
                scheduled = datetime.combine(service_date, datetime.min.time()).replace(
                    hour=hour
                )
                history.append(
                    StopTime(
                        route_id=route.id,
                        bus_id=buses[0].id,
                        stop_id=stop_lookup["Mattuthavani"].id,
                        scheduled_arrival=scheduled,
                        actual_arrival=scheduled + timedelta(minutes=delay),
                        delay_minutes=delay,
                        speed_kmh=26,
                        distance_from_previous=route.distance_km,
                        occupancy=occupancy,
                        traffic_level=traffic,
                        service_date=service_date,
                        day_of_week=weekday,
                        hour=hour,
                        minute=0,
                    )
                )
    db.add_all(history)

    db.add_all(
        [
            Alert(
                route_id=route_by_number["21B"].id,
                title="Traffic delay · Route 21B",
                message="Traffic has increased near Anna Nagar. ETA revised by about 6 minutes. Alternative Route 11 is available.",
                severity="urgent",
                active=True,
                created_at=now,
            ),
            Alert(
                route_id=route_by_number["21B"].id,
                title="Crowd forecast updated",
                message="Predicted occupancy between 6–7 PM has increased. Consider departing 15 minutes earlier.",
                severity="info",
                active=True,
                created_at=now,
            ),
            Alert(
                route_id=route_by_number["4A"].id,
                title="Route 4A operating normally",
                message="No disruption detected. Current ETA confidence is 91%.",
                severity="good",
                active=True,
                created_at=now,
            ),
        ]
    )
    db.commit()


def dashboard_payload(db: Session) -> dict:
    buses = db.query(Bus).filter(Bus.active.is_(True)).all()
    alerts = (
        db.query(Alert)
        .filter(Alert.active.is_(True))
        .order_by(Alert.created_at.desc())
        .all()
    )
    routes = {route.id: route for route in db.query(Route).all()}
    now = datetime.now()
    occupancy = models.predict_occupancy(now.hour)
    journeys = []
    for bus in buses[:3]:
        route = routes.get(bus.route_id)
        if not route:
            continue
        eta = predict_arrival(
            speed_kmh=bus.speed_kmh or 25,
            distance_km=route.distance_km or 2.5,
            occupancy=bus.occupancy or occupancy,
            traffic_level=0.55 if now.hour in (8, 9, 17, 18, 19) else 0.3,
        )
        journeys.append(
            {
                "bus_number": bus.bus_number,
                "route_number": route.route_number,
                "title": f"{route.origin} → {route.destination}",
                "meta": f"Route {route.route_number} · {route.stop_count} stops · {route.distance_km} km",
                "eta_minutes": eta["eta_minutes"],
            }
        )
    return {
        "tracked_buses": len(buses),
        "eta_accuracy": 98.2,
        "average_delay": 12,
        "crowd_level": crowd_band(occupancy),
        "active_alerts": len(alerts),
        "journeys": journeys,
        "alerts": [
            {
                "id": alert.id,
                "title": alert.title,
                "message": alert.message,
                "severity": alert.severity,
            }
            for alert in alerts
        ],
    }


def compare_routes(db: Session, from_stop: str, to_stop: str) -> list[dict]:
    routes = (
        db.query(Route)
        .filter(Route.origin.ilike(f"%{from_stop}%"))
        .all()
    )
    if not routes:
        routes = db.query(Route).filter(Route.origin.ilike("%Town Hall%")).all()
        if to_stop.lower().find("mattu") < 0:
            routes = db.query(Route).all()[:3]

    cards = []
    now = datetime.now()
    traffic = 0.55 if now.hour in (8, 9, 17, 18, 19) else 0.32
    for route in routes[:3]:
        occupancy = models.predict_occupancy(now.hour)
        eta = predict_arrival(
            speed_kmh=26 if route.transfers == 0 else 22,
            distance_km=route.distance_km or 3,
            occupancy=occupancy + route.transfers * 0.08,
            traffic_level=traffic,
        )
        score = comfort_score(
            eta["travel_time_minutes"],
            occupancy + route.transfers * 0.08,
            route.transfers or 0,
        )
        cards.append(
            {
                "route_number": route.route_number,
                "label": f"ROUTE · {route.route_number}",
                "title": f"{route.origin} → {route.destination}",
                "comfort": score,
                "travel_time": eta["eta_minutes"],
                "transfers": route.transfers or 0,
                "crowd": crowd_band(occupancy + route.transfers * 0.08),
                "eta_confidence": eta["confidence"],
                "highlight": False,
            }
        )
    if cards:
        best = max(cards, key=lambda item: item["comfort"])
        best["highlight"] = True
        if best["crowd"] == "Low":
            best["badge"] = "LOW CROWD"
        elif best["crowd"] == "Medium":
            best["badge"] = "BALANCED"
        else:
            best["badge"] = "FASTEST"
    return cards


def tracking_payload(db: Session, route_number: str = "21B") -> dict:
    route = db.query(Route).filter(Route.route_number == route_number).first()
    if not route:
        route = db.query(Route).first()
    bus = (
        db.query(Bus)
        .filter(Bus.route_id == route.id, Bus.active.is_(True))
        .first()
    )
    occupancy = bus.occupancy if bus else models.predict_occupancy(datetime.now().hour)
    eta = predict_arrival(
        speed_kmh=bus.speed_kmh if bus else 28,
        distance_km=max(0.8, (route.distance_km or 2.8) * (1 - (bus.progress or 0.6))),
        occupancy=occupancy,
        traffic_level=0.5,
    )
    remaining = [
        {"name": "Anna Nagar", "eta": "2 min · approaching", "active": True},
        {"name": "KK Nagar", "eta": "5 min", "active": False},
        {"name": "Arappalayam", "eta": "7 min", "active": False},
        {"name": "Mattuthavani", "eta": f"{int(eta['eta_minutes'])} min · destination", "active": False},
    ]
    return {
        "route_number": route.route_number,
        "title": f"{route.origin} → {route.destination}",
        "status": bus.status if bus else "ON TIME",
        "eta_minutes": eta["eta_minutes"],
        "arrival_time": eta["arrival_time"],
        "speed_kmh": bus.speed_kmh if bus else 28,
        "distance_km": round(max(0.6, (route.distance_km or 2.8) * (1 - (bus.progress or 0.6))), 1),
        "occupancy_pct": int((occupancy or 0.6) * 100),
        "progress_pct": int((bus.progress if bus else 0.68) * 100),
        "stops": remaining,
    }


def crowd_payload(db: Session, route_number: str) -> dict:
    route = db.query(Route).filter(Route.route_number == route_number).first()
    hours = [7, 9, 11, 13, 15, 17, 18, 19, 21]
    weekday = datetime.now().weekday()
    forecast = []
    for hour in hours:
        occupancy = models.predict_occupancy(hour, weekday)
        row = (
            db.query(StopTime)
            .filter(StopTime.hour == hour)
            .order_by(StopTime.service_date.desc())
            .first()
        )
        if route and row and row.route_id == route.id and row.occupancy:
            occupancy = (occupancy + row.occupancy) / 2
        forecast.append(
            {
                "hour": hour,
                "label": datetime.now().replace(hour=hour, minute=0).strftime("%I %p").lstrip("0"),
                "occupancy": round(occupancy, 2),
                "percent": int(occupancy * 100),
            }
        )
    lowest = min(forecast, key=lambda item: item["occupancy"])
    highest = max(forecast, key=lambda item: item["occupancy"])
    now_occ = models.predict_occupancy(datetime.now().hour, weekday)
    return {
        "route_number": route.route_number if route else route_number,
        "current_level": crowd_band(now_occ),
        "confidence": 91,
        "forecast": forecast,
        "advice": [
            {
                "title": "Best window",
                "message": f"{lowest['label']} has the lowest predicted occupancy.",
            },
            {
                "title": "Peak window",
                "message": f"{highest['label']} may have standing-only conditions.",
            },
            {
                "title": "Accessible travel",
                "message": "For vulnerable riders, consider the lower-crowd window.",
            },
        ],
    }


def chat_reply(db: Session, message: str) -> str:
    text = message.lower()
    dash = dashboard_payload(db)
    track = tracking_payload(db, "21B")
    crowd = crowd_payload(db, "21B")
    if "crowd" in text or "crowded" in text:
        return (
            f"Current prediction for Route 21B is {crowd['current_level'].lower()}. "
            "The 6–7 PM window is expected to be busier, so a lower-crowd alternative is Route 4A."
        )
    if "delay" in text or "late" in text:
        return (
            f"Route 21B is currently about {track['eta_minutes']} minutes from the next destination. "
            "Route 11 is available as an alternative if traffic keeps building."
        )
    if "leave" in text or "reach" in text or "9" in text:
        plan = recommend_departure("09:00", 24, 6, 10)
        return (
            f"Based on current traffic and predicted crowding, leave around "
            f"{plan['recommended_departure']} with a {plan['safety_buffer']}-minute safety buffer."
        )
    if "cancel" in text or "alternative" in text:
        return (
            "If your bus is cancelled, compare Route 11 + 4A against 21B using travel time, "
            "transfers and crowd level from the Compare Routes page."
        )
    if "fast" in text or "mattuthavani" in text or "route" in text:
        cards = compare_routes(db, "Town Hall", "Mattuthavani")
        best = cards[0] if cards else None
        if best:
            return (
                f"Route {best['route_number']} is currently estimated at {best['travel_time']} minutes "
                f"with {best['crowd'].lower()} crowding and comfort score {best['comfort']}/100."
            )
    return (
        f"I can help compare routes, check live ETAs, forecast crowding and suggest when to leave. "
        f"Right now {dash['tracked_buses']} buses are tracked and network crowd is {dash['crowd_level']}."
    )
