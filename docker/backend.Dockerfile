FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY ml_engine ./ml_engine
COPY simulator ./simulator
COPY data ./data
COPY docs ./docs

EXPOSE 8000

CMD ["python", "-m", "backend.run_server", "--host", "0.0.0.0", "--port", "8000", "--strict-port"]
