from datetime import datetime, timedelta

from app.ml.predictor import models


def predict_arrival(
    speed_kmh: float,
    distance_km: float,
    occupancy: float,
    traffic_level: float,
) -> dict:
    now = datetime.now()
    travel_time_minutes = (distance_km / max(speed_kmh, 1.0)) * 60
    delay = models.predict_delay(
        hour=now.hour,
        minute=now.minute,
        day_of_week=now.weekday(),
        speed_kmh=speed_kmh,
        occupancy=occupancy,
        traffic_level=traffic_level,
        distance_from_previous=distance_km,
    )
    total_minutes = travel_time_minutes + delay
    arrival = now + timedelta(minutes=total_minutes)
    confidence = max(72.0, min(97.0, 96.0 - delay * 1.4))
    return {
        "travel_time_minutes": round(travel_time_minutes, 1),
        "predicted_delay_minutes": round(delay, 1),
        "eta_minutes": round(total_minutes, 1),
        "arrival_time": arrival.strftime("%I:%M %p"),
        "confidence": round(confidence, 1),
    }


def recommend_departure(
    required_arrival: str,
    travel_minutes: float,
    predicted_delay: float,
    safety_buffer: int = 10,
) -> dict:
    target = datetime.strptime(required_arrival, "%H:%M")
    total = int(round(travel_minutes + predicted_delay + safety_buffer))
    recommended = target - timedelta(minutes=total)
    options = []
    for offset, label in (
        (-15, "Early · Low crowd"),
        (0, "Recommended ✓"),
        (15, "Risk · Traffic rising"),
        (30, "High delay risk"),
    ):
        when = recommended + timedelta(minutes=offset)
        options.append(
            {
                "time": when.strftime("%I:%M %p"),
                "label": label,
                "recommended": offset == 0,
            }
        )
    return {
        "required_arrival": required_arrival,
        "travel_minutes": round(travel_minutes, 1),
        "predicted_delay": round(predicted_delay, 1),
        "safety_buffer": safety_buffer,
        "recommended_departure": recommended.strftime("%I:%M %p"),
        "confidence": max(70.0, min(92.0, 90.0 - predicted_delay)),
        "options": options,
    }
