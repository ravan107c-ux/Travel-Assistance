from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from app.config import settings


ETA_FEATURES = [
    "hour",
    "minute",
    "day_of_week",
    "speed_kmh",
    "occupancy",
    "traffic_level",
    "distance_from_previous",
]

CROWD_FEATURES = [
    "hour",
    "day_of_week",
    "traffic_level",
    "is_weekend",
]


def generate_training_frame(rows: int = 4000) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    hour = rng.integers(5, 23, size=rows)
    minute = rng.integers(0, 60, size=rows)
    day_of_week = rng.integers(0, 7, size=rows)
    speed_kmh = rng.uniform(8, 42, size=rows)
    occupancy = np.clip(
        0.18
        + 0.55 * ((hour >= 7) & (hour <= 9)).astype(float)
        + 0.65 * ((hour >= 17) & (hour <= 19)).astype(float)
        + rng.normal(0, 0.08, size=rows),
        0.05,
        0.98,
    )
    traffic_level = np.clip(
        0.2
        + 0.45 * ((hour >= 8) & (hour <= 10)).astype(float)
        + 0.55 * ((hour >= 17) & (hour <= 20)).astype(float)
        + rng.normal(0, 0.07, size=rows),
        0.05,
        0.99,
    )
    distance_from_previous = rng.uniform(0.4, 4.8, size=rows)
    is_weekend = (day_of_week >= 5).astype(int)

    delay = (
        1.2
        + traffic_level * 9.5
        + occupancy * 3.4
        + (distance_from_previous / np.maximum(speed_kmh, 8)) * 18
        + ((hour >= 17) & (hour <= 19)).astype(float) * 2.8
        - is_weekend * 1.4
        + rng.normal(0, 0.7, size=rows)
    )
    delay = np.clip(delay, 0, 28)

    return pd.DataFrame(
        {
            "hour": hour,
            "minute": minute,
            "day_of_week": day_of_week,
            "speed_kmh": speed_kmh,
            "occupancy": occupancy,
            "traffic_level": traffic_level,
            "distance_from_previous": distance_from_previous,
            "is_weekend": is_weekend,
            "delay_minutes": delay,
        }
    )


def train_and_save_models(
    eta_path: Path | None = None,
    crowd_path: Path | None = None,
) -> tuple[XGBRegressor, XGBRegressor]:
    eta_path = Path(eta_path or settings.MODEL_PATH)
    crowd_path = Path(crowd_path or settings.CROWD_MODEL_PATH)
    eta_path.parent.mkdir(parents=True, exist_ok=True)

    data = generate_training_frame()

    eta_model = XGBRegressor(
        n_estimators=180,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
        n_jobs=2,
    )
    eta_model.fit(data[ETA_FEATURES], data["delay_minutes"])
    eta_model.save_model(eta_path)

    crowd_model = XGBRegressor(
        n_estimators=140,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.9,
        random_state=42,
        n_jobs=2,
    )
    crowd_model.fit(data[CROWD_FEATURES], data["occupancy"])
    crowd_model.save_model(crowd_path)
    return eta_model, crowd_model


class TransitModels:
    def __init__(self) -> None:
        self.eta_model = XGBRegressor()
        self.crowd_model = XGBRegressor()
        self._load_or_train()

    def _load_or_train(self) -> None:
        eta_path = Path(settings.MODEL_PATH)
        crowd_path = Path(settings.CROWD_MODEL_PATH)
        if eta_path.exists() and crowd_path.exists():
            self.eta_model.load_model(eta_path)
            self.crowd_model.load_model(crowd_path)
            return
        self.eta_model, self.crowd_model = train_and_save_models(eta_path, crowd_path)

    def predict_delay(
        self,
        hour: int,
        minute: int,
        day_of_week: int,
        speed_kmh: float,
        occupancy: float,
        traffic_level: float,
        distance_from_previous: float,
    ) -> float:
        frame = pd.DataFrame(
            [
                {
                    "hour": hour,
                    "minute": minute,
                    "day_of_week": day_of_week,
                    "speed_kmh": speed_kmh,
                    "occupancy": occupancy,
                    "traffic_level": traffic_level,
                    "distance_from_previous": distance_from_previous,
                }
            ]
        )
        value = float(self.eta_model.predict(frame[ETA_FEATURES])[0])
        return max(0.0, value)

    def predict_occupancy(
        self,
        hour: int,
        day_of_week: int | None = None,
        traffic_level: float = 0.45,
    ) -> float:
        now = datetime.now()
        if day_of_week is None:
            day_of_week = now.weekday()
        frame = pd.DataFrame(
            [
                {
                    "hour": hour,
                    "day_of_week": day_of_week,
                    "traffic_level": traffic_level,
                    "is_weekend": int(day_of_week >= 5),
                }
            ]
        )
        value = float(self.crowd_model.predict(frame[CROWD_FEATURES])[0])
        return float(np.clip(value, 0.05, 0.98))

    def crowd_label(self, occupancy: float) -> str:
        if occupancy < 0.4:
            return "Low"
        if occupancy < 0.7:
            return "Medium"
        return "High"


models = TransitModels()


class ETAPredictor:
    FEATURES = ETA_FEATURES

    def predict(self, **kwargs) -> float:
        return models.predict_delay(**kwargs)
