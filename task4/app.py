"""Flask web application for VisionGuard predictions."""

import os
from pathlib import PurePath

import requests
from flask import Flask, jsonify, render_template, request

if __package__:
    from .db import add_prediction, initialise, recent_predictions
    from .inference import classify_image, load_champion_model
else:
    from db import add_prediction, initialise, recent_predictions
    from inference import classify_image, load_champion_model

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "webp", "gif"}
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
MODEL_URI = os.getenv("MODEL_URI", "models:/VisionGuard@champion")
MODEL_API_URL = os.getenv("MODEL_API_URL", "").rstrip("/")
API_KEY = os.getenv("API_KEY", "")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    initialise()
    if not MODEL_API_URL:
        load_champion_model()

    def api_request_is_authorized() -> bool:
        return not API_KEY or request.headers.get("X-API-Key") == API_KEY

    def validate_upload():
        uploaded = request.files.get("image")
        if uploaded is None or not uploaded.filename:
            return None, "Please choose an image file."
        suffix = PurePath(uploaded.filename).suffix.lower().lstrip(".")
        if suffix not in ALLOWED_EXTENSIONS:
            return None, "Only JPG, PNG, BMP, WEBP, and GIF files are accepted."
        data = uploaded.read()
        if not data:
            return None, "The uploaded file is empty."
        return (uploaded, data), None

    @app.get("/")
    def upload():
        return render_template("upload.html")

    @app.post("/predict")
    def predict():
        validated, error = validate_upload()
        if error:
            return render_template("upload.html", error=error), 400
        uploaded, data = validated
        safe_name = PurePath(uploaded.filename).name
        if MODEL_API_URL:
            try:
                response = requests.post(
                    f"{MODEL_API_URL}/api/predict",
                    files={"image": (safe_name, data, uploaded.mimetype)},
                    headers={"X-API-Key": API_KEY} if API_KEY else {},
                    timeout=60,
                )
                response.raise_for_status()
                result = response.json()
            except (requests.RequestException, ValueError) as exc:
                return render_template("upload.html", error=f"Remote model API failed: {exc}"), 502
            verdict = result["decision"]
            confidence = float(result["confidence"])
        else:
            try:
                verdict, confidence = classify_image(data)
            except ValueError as exc:
                return render_template("upload.html", error=str(exc)), 400
        return render_template(
            "result.html",
            filename=safe_name,
            verdict=verdict,
            confidence=f"{confidence:.1%}",
            caveat="This is a model estimate, not proof of how an image was created.",
        )

    @app.post("/api/predict")
    def api_predict():
        if not api_request_is_authorized():
            return jsonify({"error": "Unauthorized"}), 401
        validated, error = validate_upload()
        if error:
            return jsonify({"error": error}), 400
        uploaded, data = validated
        try:
            verdict, confidence = classify_image(data)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        safe_name = PurePath(uploaded.filename).name
        add_prediction(safe_name, verdict, confidence, MODEL_URI)
        return jsonify({
            "filename": safe_name,
            "decision": verdict,
            "confidence": confidence,
            "model": MODEL_URI,
            "caveat": "This is a model estimate, not proof of how an image was created.",
        })

    @app.get("/history")
    def history():
        if MODEL_API_URL:
            try:
                response = requests.get(
                    f"{MODEL_API_URL}/api/history",
                    headers={"X-API-Key": API_KEY} if API_KEY else {},
                    timeout=15,
                )
                response.raise_for_status()
                remote_records = response.json()
                predictions = [
                    (
                        item["filename"],
                        item["decision"],
                        item["confidence"],
                        item["model"],
                        item["created_at"],
                    )
                    for item in remote_records
                ]
            except (requests.RequestException, ValueError, KeyError) as exc:
                return render_template("history.html", predictions=[],
                                       error=f"Remote history failed: {exc}"), 502
        else:
            predictions = recent_predictions()
        return render_template("history.html", predictions=predictions)

    @app.get("/api/history")
    def history_api():
        if not api_request_is_authorized():
            return jsonify({"error": "Unauthorized"}), 401
        return [
            {
                "filename": filename,
                "decision": verdict,
                "confidence": confidence,
                "model": model,
                "created_at": created_at,
            }
            for filename, verdict, confidence, model, created_at in recent_predictions()
        ]

    @app.get("/health")
    def health():
        return {"status": "ok", "model": MODEL_URI}

    @app.errorhandler(413)
    def too_large(_error):
        return render_template("upload.html", error="The image is larger than the allowed 5 MB limit."), 413

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")), debug=False)
