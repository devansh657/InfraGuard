# InfraGuard AI

InfraGuard AI is a full-stack AI security and infrastructure monitoring console. It trains machine-learning models on real network-security telemetry, exposes inference through a FastAPI backend, stores prediction history, and visualizes live risk, anomaly signals, and exploratory data analysis in a React dashboard.

## What It Does

- Trains on a protected telemetry stream stored under `data/`
- Predicts a protected elevated-risk label with a `RandomForestClassifier`
- Detects unusual telemetry with `IsolationForest`
- Explains incidents with an AI Analyst layer: root cause ranking, severity, confidence, drift, recommendations, and response playbooks
- Runs what-if simulations to compare current telemetry against proposed mitigation states
- Includes NOVA, a local voice/text operations assistant that can report risk, scan telemetry, speak briefings, and navigate the console
- Generates EDA outputs: class balance, missing values, feature distributions, correlations, confusion matrix, ROC curve, precision-recall curve, feature importance, and anomaly-score distribution
- Benchmarks multiple supervised ML models with cross-validation and holdout evaluation
- Serves model inference through FastAPI
- Stores prediction history in SQLite locally or PostgreSQL in Docker/production
- Provides a modern React dashboard with schema-driven prediction controls and EDA panels
- Replays secured telemetry samples so monitoring screens update continuously for demos
- Supports optional API-key protection for deployed API routes

## Tech Stack

- Backend: FastAPI, Pydantic, SQLAlchemy, pandas, scikit-learn, joblib
- ML: Random Forest, Isolation Forest, StandardScaler, matplotlib
- Frontend: React, Vite, Axios, Recharts, Framer Motion, Tailwind CSS
- Deployment: Docker Compose, PostgreSQL, GitHub Actions

## Project Structure

```text
backend/      FastAPI routes, services, database, security middleware
frontend/     React control-center dashboard
ml_engine/    Data loading, preprocessing, feature engineering, training, EDA
data/         Protected telemetry stream for local demos
docs/eda/     Generated EDA reports and charts
docker/       Backend/frontend Dockerfiles and nginx config
tests/        Backend integration tests
```

## Local Setup

From the project root:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

One-command local run on Windows:

```powershell
.\scripts\start_full_app.ps1
```

This starts the backend if it is not already running, waits for `/health`, and then launches the frontend dev server.

Train models and regenerate EDA:

```powershell
.venv\Scripts\python.exe -m ml_engine.train
```

Run backend:

```powershell
.venv\Scripts\python.exe -m backend.run_server
```

Run frontend in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

API docs:

```text
http://127.0.0.1:8000/docs
```

Stop the hidden backend started by the launcher:

```powershell
.\scripts\stop_backend.ps1
```

## Key API Endpoints

- `GET /health`
- `GET /live/status`
- `POST /live/tick`
- `GET /model-info`
- `GET /eda`
- `POST /diagnose`
- `POST /ai/analyze`
- `POST /ai/what-if`
- `GET /ai/nova/briefing`
- `POST /predict`
- `POST /anomaly`
- `GET /history`
- `GET /report`
- `POST /upload`

## Verification

Backend tests:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

Frontend build:

```powershell
cd frontend
npm run build
```

## Docker

After installing Docker Desktop:

```powershell
docker compose up --build
```

Services:

- Frontend: `http://localhost:5174`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

## Optional API Key

Set the same key on backend and frontend when deploying:

```text
API_KEY=replace-with-a-secret
VITE_API_KEY=replace-with-a-secret
```

## Current Model Metrics

Latest training run on 5,000 rows:

- Accuracy: `0.9960`
- Precision: `1.0000`
- Recall: `0.9852`
- F1-score: `0.9926`
- ROC AUC: `1.0000`
- Average precision: `0.9999`

The EDA report is available at `docs/eda/eda_report.md`.
The model benchmark is available at `docs/eda/model_benchmark.md`.
The model card is available at `docs/model_card.md`.

## Publish Checklist

See `docs/publish_checklist.md` for the completed verification list and final deployment checks.
