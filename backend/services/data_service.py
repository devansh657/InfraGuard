from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd
from fastapi import UploadFile

from backend.config import get_settings
from backend.schemas.request_models import MetricsRequest
from backend.schemas.response_models import (
    AnomalyResponse,
    FailurePredictionResponse,
    PredictionHistoryRecord,
    ReportResponse,
    UploadResponse,
)
from backend.services.db_service import (
    fetch_recent_predictions,
    fetch_report_counts,
    insert_prediction,
)
from backend.utils.logger import get_logger


PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
REQUIRED_UPLOAD_COLUMNS = {
    "Packet_Size",
    "Transmission_Rate",
    "Latency",
    "Protocol_Type",
    "Active_Connections",
    "CPU_Usage",
    "Memory_Usage",
    "Bandwidth_Utilization",
    "Request_Response_Time",
    "Auth_Failures",
    "Access_Violations",
    "Firewall_Blocks",
    "IDS_Alerts",
    "protected_risk_label",
    "DWT_Feature_1",
    "DWT_Feature_2",
    "DWT_Feature_3",
    "DWT_Feature_4",
    "DWT_Feature_5",
    "DWT_Feature_6",
    "DWT_Feature_7",
    "DWT_Feature_8",
}
logger = get_logger(__name__)


def record_prediction(
    metrics: MetricsRequest,
    failure: FailurePredictionResponse,
    anomaly: AnomalyResponse,
) -> int:
    prediction_id = insert_prediction(metrics, failure, anomaly)
    logger.info("prediction stored", extra={"prediction_id": prediction_id})
    return prediction_id


def get_prediction_history(limit: int = 100) -> list[PredictionHistoryRecord]:
    return [PredictionHistoryRecord(**row) for row in fetch_recent_predictions(limit=limit)]


def generate_incident_report() -> ReportResponse:
    counts = fetch_report_counts()
    total = counts["total_requests"]
    anomalies = counts["anomalies"]
    failures = counts["failures"]

    anomaly_rate = anomalies / total if total else 0.0
    failure_rate = failures / total if total else 0.0
    if total == 0:
        risk_level = "LOW"
    elif failure_rate >= 0.25 or anomaly_rate >= 0.35:
        risk_level = "HIGH"
    elif failure_rate >= 0.1 or anomaly_rate >= 0.15:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return ReportResponse(
        total_requests=total,
        anomalies=anomalies,
        failures=failures,
        risk_level=risk_level,
    )


async def save_uploaded_dataset(file: UploadFile) -> UploadResponse:
    if not file.filename:
        raise ValueError("Uploaded file must have a filename.")
    if not file.filename.lower().endswith(".csv"):
        raise ValueError("Only CSV uploads are supported.")

    content = await file.read()
    if not content:
        raise ValueError("Uploaded CSV is empty.")
    if len(content) > get_settings().max_request_bytes:
        raise ValueError("Uploaded CSV exceeds the 1MB request limit.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(file.filename)
    destination = UPLOAD_DIR / safe_name
    destination.write_bytes(content)

    try:
        data = pd.read_csv(destination)
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise ValueError("Uploaded file is not a valid CSV.") from exc

    missing_columns = sorted(REQUIRED_UPLOAD_COLUMNS - set(data.columns))
    if missing_columns:
        destination.unlink(missing_ok=True)
        raise ValueError("Telemetry package is missing required protected schema fields.")

    return UploadResponse(
        filename="validated_telemetry_upload.csv",
        rows=len(data),
        upload_id=hashlib.sha256(content).hexdigest()[:16],
        message="Telemetry package uploaded and validated successfully.",
    )


def _safe_filename(filename: str) -> str:
    name = Path(filename).name
    sanitized = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    return sanitized or "upload.csv"
