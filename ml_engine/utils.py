"""Shared constants and persistence helpers for the InfraGuard ML engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib


RANDOM_STATE = 42

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
NETWORK_DATASET_PATH = DATA_DIR / "protected_telemetry_stream.csv"
ML_ENGINE_DIR = PROJECT_ROOT / "ml_engine"
MODELS_DIR = ML_ENGINE_DIR / "models"
REPORTS_DIR = PROJECT_ROOT / "docs" / "eda"

ANOMALY_MODEL_PATH = MODELS_DIR / "anomaly_model.pkl"
FAILURE_MODEL_PATH = MODELS_DIR / "failure_model.pkl"
MODEL_METADATA_PATH = MODELS_DIR / "model_metadata.json"

TARGET_COLUMN = "protected_risk_label"

BASE_NUMERIC_FEATURES = [
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
    "DWT_Feature_1",
    "DWT_Feature_2",
    "DWT_Feature_3",
    "DWT_Feature_4",
    "DWT_Feature_5",
    "DWT_Feature_6",
    "DWT_Feature_7",
    "DWT_Feature_8",
]
ENGINEERED_FEATURES = [
    "rolling_mean_cpu_usage",
    "rolling_mean_latency",
    "rolling_mean_request_response_time",
    "rolling_mean_ids_alerts",
    "latency_spike_flag",
    "auth_failure_burst_flag",
    "ids_alert_burst_flag",
    "bandwidth_pressure_flag",
]
FEATURE_COLUMNS = BASE_NUMERIC_FEATURES + ENGINEERED_FEATURES
SCALED_FEATURE_COLUMNS = FEATURE_COLUMNS.copy()

DEFAULT_DATASET_PATH = NETWORK_DATASET_PATH

FEATURE_DESCRIPTIONS = {
    "Packet_Size": "Network packet size observed in the sample.",
    "Transmission_Rate": "Observed network transmission rate.",
    "Latency": "Network latency for the sample.",
    "Protocol_Type": "Encoded protocol category from the dataset.",
    "Active_Connections": "Number of active network connections.",
    "CPU_Usage": "Host CPU utilization signal.",
    "Memory_Usage": "Host memory usage signal.",
    "Bandwidth_Utilization": "Network bandwidth utilization.",
    "Request_Response_Time": "Round-trip request/response timing.",
    "Auth_Failures": "Authentication failures observed in the sample.",
    "Access_Violations": "Access policy violations observed in the sample.",
    "Firewall_Blocks": "Firewall block events observed in the sample.",
    "IDS_Alerts": "Intrusion detection alerts observed in the sample.",
    "DWT_Feature_1": "Wavelet-derived dataset feature 1.",
    "DWT_Feature_2": "Wavelet-derived dataset feature 2.",
    "DWT_Feature_3": "Wavelet-derived dataset feature 3.",
    "DWT_Feature_4": "Wavelet-derived dataset feature 4.",
    "DWT_Feature_5": "Wavelet-derived dataset feature 5.",
    "DWT_Feature_6": "Wavelet-derived dataset feature 6.",
    "DWT_Feature_7": "Wavelet-derived dataset feature 7.",
    "DWT_Feature_8": "Wavelet-derived dataset feature 8.",
}


def ensure_models_dir() -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR


def ensure_reports_dir() -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR


def save_pickle(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(payload, path)


def load_pickle(path: Path) -> Any:
    return joblib.load(path)


def resolve_project_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate
