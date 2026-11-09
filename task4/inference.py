"""VisionGuard inference with training-compatible preprocessing."""

import os
from functools import lru_cache
from io import BytesIO

import mlflow
import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError

IMAGE_SIZE = (160, 160)


@lru_cache(maxsize=1)
def load_champion_model():
    """Load the configured model once per process."""
    model_path = os.getenv("MODEL_PATH")
    if model_path:
        return tf.keras.models.load_model(model_path)
    model_uri = os.getenv("MODEL_URI", "models:/VisionGuard@champion")
    return mlflow.tensorflow.load_model(model_uri)


def classify_image(data: bytes) -> tuple[str, float]:
    """Decode and classify image bytes using the training preprocessing."""
    try:
        image = Image.open(BytesIO(data)).convert("RGB").resize(IMAGE_SIZE)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("The uploaded file is not a readable image.") from exc
    array = np.asarray(image, dtype="float32") / 255.0
    score = float(load_champion_model().predict(np.expand_dims(array, 0), verbose=0)[0, 0])
    threshold = float(os.getenv("MODEL_THRESHOLD", "0.5"))
    return ("ai" if score >= threshold else "real"), score
