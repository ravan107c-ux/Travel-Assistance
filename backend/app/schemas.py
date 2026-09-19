from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "English"


class ChatResponse(BaseModel):
    reply: str


class ETAResponse(BaseModel):
    route_number: str
    stop_name: str
    eta_minutes: float
    arrival_time: str
    predicted_delay_minutes: float
    travel_time_minutes: float
    confidence: float


class DepartureRequest(BaseModel):
    route_number: str = "21B"
    origin: str = "Town Hall"
    destination: str = "Anna Nagar College"
    required_arrival: str = Field(..., examples=["09:00"])
    safety_buffer: int = 10


class RouteCompareRequest(BaseModel):
    from_stop: str
    to_stop: str
