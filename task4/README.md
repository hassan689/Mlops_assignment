# Task 4: Flask Web Application

[![VisionGuard CI](https://github.com/hassan689/Mlops_assignment/actions/workflows/ci.yml/badge.svg)](https://github.com/hassan689/Mlops_assignment/actions/workflows/ci.yml)

The app loads the MLflow champion model once at startup. It preprocesses images
as training does: RGB conversion, resize to `160x160`, float32 conversion, and
division by `255`. Upload bytes are decoded in memory and are never saved.

Run from the assignment root with the virtual environment active:

```powershell
$env:MODEL_URI="models:/VisionGuard@champion"
$env:DATABASE_PATH="C:\Users\JT GAMING\Desktop\Projects\Mlops\assignment2\task4\history.db"
python task4\app.py
```

Open `http://127.0.0.1:8000`. The health check is
`http://127.0.0.1:8000/health`.

Loading a model for every request is unacceptable because model loading is slow,
uses substantial memory, and causes unnecessary latency. Training and serving
preprocessing must match because different color channels, image sizes, or
scaling change the input distribution and make the model's predictions
unreliable.

The application runs with Flask debug mode disabled. Production deployments
should use a production WSGI server rather than Flask's development server.

## Task 5: Queryable prediction history

Every successful prediction inserts a permanent SQLite record containing the
filename, decision, confidence, model URI, and UTC timestamp. The records are
shown at `/history` and are also queryable as JSON at `/api/history`.

## Task 6: Docker and Compose

Copy `.env.example` to `.env`, change the password, and export the champion
Keras model to `task4/model/`. The model directory is mounted
read-only, keeping large model files and secrets out of the image.

```powershell
python task4\export_model.py
Copy-Item .env.example .env
docker compose up --build
```

The web container is non-root and waits for PostgreSQL's health check. The
database has a named volume and no published host port; the web service reaches
it by the Compose service name `db`. Dependencies are copied before source
code so changing application code reuses the expensive dependency layer.
The slim Python base, pip's disabled cache, and `.dockerignore` reduce image
size. TensorFlow is installed from the standard Linux package because this
CPU-only application does not need GPU libraries.

The CI workflow runs syntax checks for two Python versions and builds the
Docker image. GitHub Actions secrets belong in repository or environment
settings, never in the workflow file.

## Task 7/8: Render API deployment

The Render blueprint is in `render.yaml`. Create a Render Blueprint from the
GitHub repository, deploy the generated model and database services, then copy
the generated `API_KEY` from the web service environment settings. The public
API is:

```text
https://<render-service>.onrender.com/api/predict
```

Test it with Postman using `POST`, header `X-API-Key`, and a multipart form
field named `image`. For local Flask integration, set:

```powershell
$env:MODEL_API_URL="https://<render-service>.onrender.com"
$env:API_KEY="<Render-generated-key>"
python task4\app.py
```

The local UI then forwards uploads to Render, while the Render API persists
each result in PostgreSQL.
