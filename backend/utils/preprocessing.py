from __future__ import annotations

from typing import Any, Protocol

import pandas as pd

from backend.schemas.request_models import MetricsRequest


class _Scaler(Protocol):
    """Structural type for a fitted sklearn-style scaler."""

    def transform(self, X: pd.DataFrame) -> Any:
        ...


def build_model_features(
    metrics: MetricsRequest,
    scaler: _Scaler,
    feature_columns: list[str],
    scaled_feature_columns: list[str],
    feature_config: dict[str, Any],
) -> pd.DataFrame:
    row = metrics.to_feature_dict()
    row.update(_engineered_single_row(row, feature_config))
    features = pd.DataFrame([row])
    features[scaled_feature_columns] = scaler.transform(features[scaled_feature_columns])
    return features[feature_columns]


def _engineered_single_row(row: dict[str, float], feature_config: dict[str, Any]) -> dict[str, float]:
    return {
        "rolling_mean_cpu_usage": row["CPU_Usage"],
        "rolling_mean_latency": row["Latency"],
        "rolling_mean_request_response_time": row["Request_Response_Time"],
        "rolling_mean_ids_alerts": row["IDS_Alerts"],
        "latency_spike_flag": float(row["Latency"] > float(feature_config["latency_spike_threshold"])),
        "auth_failure_burst_flag": float(
            row["Auth_Failures"] > float(feature_config["auth_failure_burst_threshold"])
        ),
        "ids_alert_burst_flag": float(
            row["IDS_Alerts"] > float(feature_config["ids_alert_burst_threshold"])
        ),
        "bandwidth_pressure_flag": float(
            row["Bandwidth_Utilization"] > float(feature_config["bandwidth_pressure_threshold"])
        ),
    }
