"""Isolation Forest anomaly detection model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

try:
    from .utils import ANOMALY_MODEL_PATH, FEATURE_COLUMNS, RANDOM_STATE, save_pickle
except ImportError:
    from utils import ANOMALY_MODEL_PATH, FEATURE_COLUMNS, RANDOM_STATE, save_pickle


def train_anomaly_model(features: pd.DataFrame) -> IsolationForest:
    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    model.fit(features)
    return model


def _raw_anomaly_scores(model: IsolationForest, features: pd.DataFrame) -> np.ndarray:
    return -model.decision_function(features)


def get_anomaly_score_bounds(
    model: IsolationForest,
    reference_features: pd.DataFrame,
) -> tuple[float, float]:
    raw_scores = _raw_anomaly_scores(model, reference_features)
    return float(np.min(raw_scores)), float(np.max(raw_scores))


def normalize_anomaly_scores(
    raw_scores: np.ndarray,
    score_min: float,
    score_max: float,
) -> np.ndarray:
    if score_max <= score_min:
        return np.zeros_like(raw_scores, dtype=float)
    normalized = (raw_scores - score_min) / (score_max - score_min)
    return np.clip(normalized, 0.0, 1.0)


def predict_anomalies(
    model: IsolationForest,
    features: pd.DataFrame,
    score_min: float | None = None,
    score_max: float | None = None,
) -> pd.DataFrame:
    raw_scores = _raw_anomaly_scores(model, features)
    if score_min is None:
        score_min = float(np.min(raw_scores))
    if score_max is None:
        score_max = float(np.max(raw_scores))

    labels = (model.predict(features) == -1).astype(int)
    scores = normalize_anomaly_scores(raw_scores, score_min, score_max)

    return pd.DataFrame(
        {
            "anomaly_score": scores,
            "anomaly_label": labels,
        },
        index=features.index,
    )


def format_anomaly_output(score: float, anomaly_label: int) -> dict[str, Any]:
    return {
        "is_anomaly": bool(anomaly_label),
        "score": round(float(score), 4),
    }


def save_anomaly_model(
    model: IsolationForest,
    scaler: Any,
    path: Path = ANOMALY_MODEL_PATH,
    feature_columns: list[str] | None = None,
    scaled_feature_columns: list[str] | None = None,
    base_feature_columns: list[str] | None = None,
    feature_config: dict[str, Any] | None = None,
    feature_defaults: dict[str, float] | None = None,
    feature_schema: list[dict[str, Any]] | None = None,
    score_reference_features: pd.DataFrame | None = None,
) -> None:
    reference = score_reference_features
    if reference is None:
        score_min = 0.0
        score_max = 1.0
    else:
        score_min, score_max = get_anomaly_score_bounds(model, reference)

    bundle = {
        "model": model,
        "scaler": scaler,
        "feature_columns": feature_columns or FEATURE_COLUMNS,
        "scaled_feature_columns": scaled_feature_columns or feature_columns or FEATURE_COLUMNS,
        "base_feature_columns": base_feature_columns or [],
        "feature_config": feature_config or {},
        "feature_defaults": feature_defaults or {},
        "feature_schema": feature_schema or [],
        "score_min": score_min,
        "score_max": score_max,
    }
    save_pickle(bundle, path)


if __name__ == "__main__":
    try:
        from .dataset_loader import load_dataset
        from .feature_engineering import add_time_series_features
        from .preprocess import clean_dataset, split_and_scale
    except ImportError:
        from dataset_loader import load_dataset
        from feature_engineering import add_time_series_features
        from preprocess import clean_dataset, split_and_scale

    frame = add_time_series_features(clean_dataset(load_dataset()))
    split = split_and_scale(frame)
    fitted_model = train_anomaly_model(split.X_train)
    results = predict_anomalies(fitted_model, split.X_test)
    print(results.head())
