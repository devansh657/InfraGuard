# InfraGuard AI Deployment Notes

## Local Stable Run

One-command Windows launcher:

```powershell
.\scripts\start_full_app.ps1
```

Stop backend launched by the script:

```powershell
.\scripts\stop_backend.ps1
```

Regenerate models and EDA artifacts:

```powershell
.venv\Scripts\python.exe -m ml_engine.train
```

Backend:

```powershell
.venv\Scripts\python.exe -m backend.run_server
```

Frontend:

```powershell
cd frontend
npm run dev
```

## Docker Compose

```powershell
docker compose up --build
```

Services:

- Frontend: http://localhost:5174
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs
- EDA assets: http://localhost:8000/eda-assets/roc_curve.png
- Postgres: localhost:5432

## Core API Endpoints

- `GET /health`
- `GET /model-info`
- `GET /eda`
- `POST /diagnose`
- `POST /predict`
- `POST /anomaly`
- `GET /history`
- `GET /report`
- `POST /upload`

## Production Environment Variables

- `APP_ENV=production`
- `DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DB`
- `FRONTEND_ORIGINS=https://your-frontend-domain.com`
- `RATE_LIMIT_PER_MINUTE=60`
- `RATE_LIMIT_WRITE_PER_MINUTE=10`
- `MAX_REQUEST_BYTES=1048576`
- `API_KEY=replace-with-a-secret` optional API-key protection

## Render / AWS Backend

Use the backend Dockerfile or run:

```bash
python -m backend.run_server --host 0.0.0.0 --port $PORT --strict-port
```

Provide `DATABASE_URL` for Supabase, AWS RDS, Render Postgres, or another managed PostgreSQL database.

## Vercel Frontend

Set:

```text
VITE_API_BASE_URL=https://your-backend-domain.com
VITE_API_KEY=replace-with-a-secret
```

Build command:

```text
npm run build
```

Output directory:

```text
dist
```
