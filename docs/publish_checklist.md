# InfraGuard AI Publish Checklist

## Completed

- Protected telemetry stream is stored under `data/`
- ML training pipeline uses the protected telemetry schema and protected elevated-risk target
- Random Forest failure/anomalous-load model trained and saved
- Isolation Forest anomaly model trained and saved
- Model metadata saved in `ml_engine/models/model_metadata.json`
- EDA artifacts generated in `docs/eda`
- Model benchmark artifacts generated in `docs/eda/model_benchmark.md`
- Model card added in `docs/model_card.md`
- FastAPI backend exposes model, EDA, prediction, anomaly, diagnosis, history, report, upload, and health endpoints
- SQLite works for local persistence
- PostgreSQL is configured for Docker Compose and production
- React frontend builds successfully
- Prediction Lab is schema-driven from `/model-info`
- System Insights displays EDA charts and metrics
- Optional API-key protection is supported with `API_KEY` and `VITE_API_KEY`
- Security middleware includes request-size guard, rate limiting, CORS controls, and security headers
- GitHub Actions CI is present for backend tests and frontend build
- Dockerfiles and Docker Compose are present
- Top-level README and deployment notes are present

## Verified Locally

- `python -m ml_engine.train`
- `python -m pytest -q`
- `npm run build`
- Backend smoke test for `/model-info`, `/diagnose`, `/eda`, `/history`, and `/eda-assets/roc_curve.png`

## Needs External Tool Verification

- Docker Compose build and run, because Docker Desktop is not installed on this machine
- Production deployment environment variables for the final hosting provider
- Public domain CORS value in `FRONTEND_ORIGINS`
- Production secret value for `API_KEY`

## Before Publishing Publicly

- Do not commit `.env`
- Do not commit local runtime databases
- Add screenshots or a short demo GIF to the README if desired
- Install Docker Desktop and run `docker compose up --build`
- If deploying, set `VITE_API_BASE_URL` to the real backend URL
