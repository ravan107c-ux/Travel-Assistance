from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True)
    route_number = Column(String(20), unique=True, index=True)
    route_name = Column(String(150))
    origin = Column(String(150), index=True)
    destination = Column(String(150), index=True)
    distance_km = Column(Float, default=3.0)
    stop_count = Column(Integer, default=6)
    transfers = Column(Integer, default=0)

    buses = relationship("Bus", back_populates="route")
    alerts = relationship("Alert", back_populates="route")


class Stop(Base):
    __tablename__ = "stops"

    id = Column(Integer, primary_key=True)
    stop_name = Column(String(150), unique=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)


class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True)
    bus_number = Column(String(30), unique=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"))
    capacity = Column(Integer, default=50)
    active = Column(Boolean, default=True)
    speed_kmh = Column(Float, default=28.0)
    occupancy = Column(Float, default=0.62)
    latitude = Column(Float)
    longitude = Column(Float)
    progress = Column(Float, default=0.5)
    status = Column(String(30), default="ON TIME")

    route = relationship("Route", back_populates="buses")
    positions = relationship("BusPosition", back_populates="bus")


class StopTime(Base):
    __tablename__ = "stop_times"

    id = Column(BigInteger, primary_key=True)
    route_id = Column(Integer, ForeignKey("routes.id"), index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"))
    stop_id = Column(Integer, ForeignKey("stops.id"))
    scheduled_arrival = Column(DateTime)
    actual_arrival = Column(DateTime)
    delay_minutes = Column(Float)
    speed_kmh = Column(Float)
    distance_from_previous = Column(Float)
    occupancy = Column(Float)
    traffic_level = Column(Float)
    service_date = Column(Date)
    day_of_week = Column(Integer)
    hour = Column(Integer)
    minute = Column(Integer)


class BusPosition(Base):
    __tablename__ = "bus_positions"

    id = Column(BigInteger, primary_key=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    speed_kmh = Column(Float)
    occupancy = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    bus = relationship("Bus", back_populates="positions")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    route_id = Column(Integer, ForeignKey("routes.id"))
    title = Column(String(200))
    message = Column(Text)
    severity = Column(String(30))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    route = relationship("Route", back_populates="alerts")
