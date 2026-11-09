"""Export the MLflow champion model for the Docker read-only model mount."""

import os
from pathlib import Path

import mlflow.tensorflow


def main() -> None:
    destination = Path(os.getenv("MODEL_EXPORT_PATH", Path(__file__).with_name("model")))
    destination.mkdir(parents=True, exist_ok=True)
    model = mlflow.tensorflow.load_model(os.getenv("MODEL_URI", "models:/VisionGuard@champion"))
    model.save(destination)
    print(f"Exported champion model to {destination}")


if __name__ == "__main__":
    main()
