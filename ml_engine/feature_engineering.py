"""Feature engineering for network-security telemetry."""

from __future__ import annotations

from typing import Any

import pandas as pd


ROLLING_WINDOW = 5
THRESHOLD_QUANTILE = 0.95


def infer_feature_config(
    data: pd.DataFrame,
    rolling_window: int = ROLLING_WINDOW,
    threshold_quantile: float = THRESHOLD_QUANTILE,
) -> dict[str, Any]:
    """Derive deterministic feature thresholds from the dataset distribution."""

    if not 0 < threshold_quantile < 1:
        raise ValueError("threshold_quantile must be between 0 and 1.")

    return {
        "rolling_window": rolling_window,
        "threshold_quantile": threshold_quantile,
        "latency_spike_threshold": float(data["Latency"].quantile(threshold_quantile)),
        "auth_failure_burst_threshold": float(data["Auth_Failures"].quantile(threshold_quantile)),
        "ids_alert_burst_threshold": float(data["IDS_Alerts"].quantile(threshold_quantile)),
        "bandwidth_pressure_threshold": float(
            data["Bandwidth_Utilization"].quantile(threshold_quantile)
        ),
    }


def add_time_series_features(
    data: pd.DataFrame,
    feature_config: dict[str, Any] | None = None,
) -> pd.DataFrame:
    config = feature_config or infer_feature_config(data)
    rolling_window = int(config["rolling_window"])
    engineered = data.sort_values("record_index").reset_index(drop=True).copy()

    engineered["rolling_mean_cpu_usage"] = (
        engineered["CPU_Usage"].rolling(window=rolling_window, min_periods=1).mean()
    )

    engineered["rolling_mean_latency"] = (
        engineered["Latency"].rolling(window=rolling_window, min_periods=1).mean()
    )
    engineered["rolling_mean_request_response_time"] = (
        engineered["Request_Response_Time"].rolling(window=rolling_window, min_periods=1).mean()
    )
    engineered["rolling_mean_ids_alerts"] = (
        engineered["IDS_Alerts"].rolling(window=rolling_window, min_periods=1).mean()
    )

    engineered["latency_spike_flag"] = (
        engineered["Latency"] > float(config["latency_spike_threshold"])
    ).astype(int)
    engineered["auth_failure_burst_flag"] = (
        engineered["Auth_Failures"] > float(config["auth_failure_burst_threshold"])
    ).astype(int)
    engineered["ids_alert_burst_flag"] = (
        engineered["IDS_Alerts"] > float(config["ids_alert_burst_threshold"])
    ).astype(int)
    engineered["bandwidth_pressure_flag"] = (
        engineered["Bandwidth_Utilization"] > float(config["bandwidth_pressure_threshold"])
    ).astype(int)

    return engineered


if __name__ == "__main__":
    try:
        from .dataset_loader import load_dataset
        from .preprocess import clean_dataset
    except ImportError:
        from dataset_loader import load_dataset
        from preprocess import clean_dataset

    frame = add_time_series_features(clean_dataset(load_dataset()))
    print(frame.tail())
