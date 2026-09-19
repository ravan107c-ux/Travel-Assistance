from pathlib import Path

import pandas as pd


INPUT = Path("data/raw")

OUTPUT = Path("data/processed/bus_data.csv")


def find_csv():

    files = list(INPUT.glob("*.csv"))

    if not files:
        raise FileNotFoundError(
            "No CSV found in data/raw"
        )

    return files[0]


def main():

    input_file = find_csv()

    print("Reading:", input_file)

    df = pd.read_csv(input_file)

    print("\nOriginal columns:")
    print(df.columns.tolist())

    # ------------------------------------------------
    # CHANGE THESE COLUMN NAMES AFTER INSPECTING
    # YOUR ACTUAL KAGGLE DATASET
    # ------------------------------------------------

    rename_map = {
        "route": "route_number",
        "bus": "bus_number",
        "stop": "stop_name",
        "scheduled_time": "scheduled_arrival",
        "actual_time": "actual_arrival",
        "speed": "speed_kmh",
        "occupancy_rate": "occupancy",
        "traffic": "traffic_level"
    }

    df = df.rename(
        columns={
            old: new
            for old, new in rename_map.items()
            if old in df.columns
        }
    )

    required = [
        "route_number",
        "bus_number",
        "stop_name"
    ]

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Missing required columns: {missing}"
        )

    if "scheduled_arrival" in df.columns:

        df["scheduled_arrival"] = pd.to_datetime(
            df["scheduled_arrival"],
            errors="coerce"
        )

    if "actual_arrival" in df.columns:

        df["actual_arrival"] = pd.to_datetime(
            df["actual_arrival"],
            errors="coerce"
        )

    if {
        "scheduled_arrival",
        "actual_arrival"
    }.issubset(df.columns):

        df["delay_minutes"] = (
            df["actual_arrival"]
            - df["scheduled_arrival"]
        ).dt.total_seconds() / 60

    if "scheduled_arrival" in df.columns:

        df["day_of_week"] = (
            df["scheduled_arrival"].dt.dayofweek
        )

        df["hour"] = (
            df["scheduled_arrival"].dt.hour
        )

        df["minute"] = (
            df["scheduled_arrival"].dt.minute
        )

        df["service_date"] = (
            df["scheduled_arrival"].dt.date
        )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT,
        index=False
    )

    print(
        f"Processed {len(df)} records"
    )

    print(
        "Saved:", OUTPUT
    )


if __name__ == "__main__":
    main()