from pathlib import Path

import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

from xgboost import XGBRegressor


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

# train_model.py is inside:
# backend/scripts/train_model.py

BASE_DIR = Path(__file__).resolve().parent.parent

DATA = BASE_DIR / "data" / "processed" / "bus_data.csv"

MODEL_DIR = BASE_DIR / "model"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# --------------------------------------------------
# FEATURES
# --------------------------------------------------

FEATURES = [
    "hour",
    "minute",
    "day_of_week",
    "speed_kmh",
    "occupancy",
    "traffic_level",
    "distance_from_previous"
]

TARGET = "delay_minutes"


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    print("=" * 50)
    print("PinkRoute AI - XGBoost Training")
    print("=" * 50)

    print(f"\nDataset:")
    print(DATA)

    # Check dataset exists
    if not DATA.exists():
        print("\nERROR: Dataset not found!")
        print(f"Expected file:\n{DATA}")
        print("\nPlease put bus_data.csv inside:")
        print(BASE_DIR / "data" / "processed")
        return

    # --------------------------------------------------
    # LOAD CSV
    # --------------------------------------------------

    print("\nLoading dataset...")

    try:
        df = pd.read_csv(
            DATA,
            encoding="utf-8-sig"
        )

    except UnicodeDecodeError:
        print("UTF-8 encoding failed. Trying Windows-1252...")

        df = pd.read_csv(
            DATA,
            encoding="cp1252"
        )

    except Exception as e:
        print("\nERROR while reading CSV:")
        print(e)
        return

    print("\nDataset loaded successfully!")

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\nAvailable columns:")
    print(list(df.columns))


    # --------------------------------------------------
    # CHECK TARGET
    # --------------------------------------------------

    if TARGET not in df.columns:

        print(
            f"\nERROR: Target column '{TARGET}' "
            "does not exist in your CSV."
        )

        print("\nYour CSV must contain:")
        print(f"    {TARGET}")

        return


    # --------------------------------------------------
    # CREATE MISSING FEATURES
    # --------------------------------------------------

    print("\nChecking feature columns...")

    for column in FEATURES:

        if column not in df.columns:

            print(
                f"Column '{column}' not found. "
                "Creating it with 0."
            )

            df[column] = 0


    # --------------------------------------------------
    # CLEAN DATA
    # --------------------------------------------------

    df = df.dropna(
        subset=[TARGET]
    )

    # Convert features to numeric
    for column in FEATURES:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Convert target to numeric
    df[TARGET] = pd.to_numeric(
        df[TARGET],
        errors="coerce"
    )

    # Replace invalid values
    df[FEATURES] = df[FEATURES].fillna(0)

    df = df.dropna(
        subset=[TARGET]
    )


    if len(df) < 10:

        print(
            "\nERROR: Not enough valid data "
            "to train the model."
        )

        print(f"Valid rows: {len(df)}")

        return


    # --------------------------------------------------
    # X AND Y
    # --------------------------------------------------

    X = df[FEATURES]

    y = df[TARGET]


    print("\nTraining data:")
    print(f"X shape: {X.shape}")
    print(f"Y shape: {y.shape}")


    # --------------------------------------------------
    # TRAIN / TEST SPLIT
    # --------------------------------------------------

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )


    # --------------------------------------------------
    # XGBOOST MODEL
    # --------------------------------------------------

    model = XGBRegressor(

        n_estimators=500,

        max_depth=7,

        learning_rate=0.05,

        subsample=0.8,

        colsample_bytree=0.8,

        objective="reg:squarederror",

        random_state=42,

        n_jobs=-1
    )


    # --------------------------------------------------
    # TRAIN
    # --------------------------------------------------

    print("\nTraining XGBoost...")

    model.fit(
        X_train,
        y_train
    )


    # --------------------------------------------------
    # PREDICTIONS
    # --------------------------------------------------

    print("\nTesting model...")

    predictions = model.predict(
        X_test
    )


    # --------------------------------------------------
    # METRICS
    # --------------------------------------------------

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = mean_squared_error(
        y_test,
        predictions
    ) ** 0.5


    print("\n" + "=" * 50)
    print("MODEL RESULTS")
    print("=" * 50)

    print(
        f"MAE  : {mae:.2f} minutes"
    )

    print(
        f"RMSE : {rmse:.2f} minutes"
    )


    # --------------------------------------------------
    # SAVE MODEL
    # --------------------------------------------------

    model_path = MODEL_DIR / "eta_xgboost.json"

    model.save_model(
        model_path
    )

    print("\nModel saved successfully!")

    print(
        f"Location:\n{model_path}"
    )

    print("\nTraining complete.")
    print("=" * 50)


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":
    main()