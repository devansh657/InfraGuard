from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Any

import pandas as pd
import numpy as np

from backend.schemas.request_models import MetricsRequest
from backend.schemas.response_models import AnalysisResponse
from backend.services.data_service import record_prediction
from backend.services.ml_service import get_ml_service


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "data" / "protected_telemetry_stream.csv"
TARGET_COLUMN = "protected_risk_label"
PUBLIC_STREAM_NAME = "secured_telemetry_stream"


class LiveReplayService:
    """Sequential replay of real telemetry rows for a live-monitoring demo."""

    def __init__(self, dataset_path: Path = DATASET_PATH) -> None:
        self.dataset_path = dataset_path
        self._frame: pd.DataFrame | None = None
        self._index = 0
        self._lock = Lock()

    def status(self) -> dict[str, Any]:
        frame = self._load_frame()
        with self._lock:
            index = self._index
        return {
            "source": PUBLIC_STREAM_NAME,
            "rows": len(frame),
            "next_record_index": index % len(frame),
            "mode": "sequential_dataset_replay",
        }

    def tick(self) -> dict[str, Any]:
        frame = self._load_frame()
        with self._lock:
            row_index = self._index % len(frame)
            self._index += 1

        row = frame.iloc[row_index]
        payload = self._row_to_payload(row)
        metrics = MetricsRequest.model_validate(payload)
        analysis = get_ml_service().analyze_metrics(metrics)
        prediction_id = record_prediction(metrics, analysis.failure, analysis.anomaly)
        actual_label = int(row[TARGET_COLUMN]) if TARGET_COLUMN in row else None

        return {
            "prediction_id": prediction_id,
            "source": PUBLIC_STREAM_NAME,
            "replay_mode": "sequential_dataset_replay",
            "record_index": int(row_index),
            "actual_label": actual_label,
            "features": payload,
            "analysis": analysis.model_dump(),
            "explanation": _build_human_explanation(payload, analysis, actual_label),
        }

    def _load_frame(self) -> pd.DataFrame:
        if self._frame is not None:
            return self._frame
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Live dataset not found: {self.dataset_path}")

        frame = pd.read_csv(self.dataset_path)
        if frame.empty:
            raise ValueError("Live dataset is empty.")
        self._frame = frame.reset_index(drop=True)
        return self._frame

    @staticmethod
    def _row_to_payload(row: pd.Series) -> dict[str, float | int]:
        payload: dict[str, float | int] = {}
        for key, value in row.items():
            if key == TARGET_COLUMN:
                continue
            if isinstance(value, (int, np.integer)):
                payload[key] = int(value)
            else:
                numeric = float(value)
                payload[key] = int(numeric) if numeric.is_integer() and key in INTEGER_COLUMNS else numeric
        return payload


INTEGER_COLUMNS = {
    "Packet_Size",
    "Protocol_Type",
    "Active_Connections",
    "Auth_Failures",
    "Access_Violations",
    "Firewall_Blocks",
    "IDS_Alerts",
}


def _build_human_explanation(
    payload: dict[str, float | int],
    analysis: AnalysisResponse,
    actual_label: int | None,
) -> str:
    predicted = analysis.failure.prediction
    probability = round(analysis.failure.failure_probability * 100, 1)
    anomaly_text = "an unusual telemetry shape" if analysis.anomaly.is_anomaly else "a familiar telemetry shape"
    label_text = "unknown" if actual_label is None else ("anomalous" if actual_label else "normal")
    top_features = ", ".join(item.feature for item in analysis.failure.explanation[:3]) or "model features"
    return (
        f"Telemetry sample has protected label {label_text}. The supervised model predicts "
        f"{'anomalous load' if predicted else 'normal load'} with {probability}% risk, "
        f"while Isolation Forest sees {anomaly_text}. Main drivers: {top_features}."
    )


_service = LiveReplayService()


def get_live_replay_service() -> LiveReplayService:
    return _service
