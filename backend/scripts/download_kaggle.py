import os
from pathlib import Path

import kaggle


DATASET = os.getenv(
    "KAGGLE_DATASET",
    "YOUR_USERNAME/YOUR_DATASET"
)

OUTPUT = Path("data/raw")

OUTPUT.mkdir(
    parents=True,
    exist_ok=True
)


def main():

    print("Downloading Kaggle dataset...")

    kaggle.api.authenticate()

    kaggle.api.dataset_download_files(
        DATASET,
        path=str(OUTPUT),
        unzip=True
    )

    print("Dataset downloaded to:", OUTPUT)


if __name__ == "__main__":
    main()