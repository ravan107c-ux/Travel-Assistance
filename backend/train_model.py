from app.ml.predictor import train_and_save_models


if __name__ == "__main__":
    eta_model, crowd_model = train_and_save_models()
    print("Saved XGBoost models:")
    print("  ETA delay model trained")
    print("  Crowd occupancy model trained")
