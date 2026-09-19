CREATE DATABASE pinkroute;

\c pinkroute;

CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    route_number VARCHAR(20) UNIQUE NOT NULL,
    route_name VARCHAR(150),
    origin VARCHAR(150),
    destination VARCHAR(150)
);

CREATE TABLE stops (
    id SERIAL PRIMARY KEY,
    stop_name VARCHAR(150) UNIQUE NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

CREATE TABLE buses (
    id SERIAL PRIMARY KEY,
    bus_number VARCHAR(30) UNIQUE NOT NULL,
    route_id INTEGER REFERENCES routes(id),
    capacity INTEGER DEFAULT 50,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE stop_times (
    id BIGSERIAL PRIMARY KEY,

    route_id INTEGER REFERENCES routes(id),
    bus_id INTEGER REFERENCES buses(id),
    stop_id INTEGER REFERENCES stops(id),

    scheduled_arrival TIMESTAMP,
    actual_arrival TIMESTAMP,

    delay_minutes DOUBLE PRECISION,

    speed_kmh DOUBLE PRECISION,
    distance_from_previous DOUBLE PRECISION,

    occupancy DOUBLE PRECISION,
    traffic_level DOUBLE PRECISION,

    service_date DATE,
    day_of_week INTEGER,
    hour INTEGER,
    minute INTEGER
);

CREATE TABLE bus_positions (
    id BIGSERIAL PRIMARY KEY,

    bus_id INTEGER REFERENCES buses(id),

    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,

    speed_kmh DOUBLE PRECISION,
    occupancy DOUBLE PRECISION,

    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,

    route_id INTEGER REFERENCES routes(id),

    title VARCHAR(200),
    message TEXT,

    severity VARCHAR(30),

    active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stop_times_route
ON stop_times(route_id);

CREATE INDEX idx_stop_times_bus
ON stop_times(bus_id);

CREATE INDEX idx_bus_positions_bus
ON bus_positions(bus_id);