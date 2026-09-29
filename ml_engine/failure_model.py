"""Random Forest failure prediction model."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

try:
    from .utils import FAILURE_MODEL_PATH, FEATURE_COLUMNS, RANDOM_STATE, save_pickle
except ImportError:
    from utils import FAILURE_MODEL_PATH, FEATURE_COLUMNS, RANDOM_STATE, save_pickle


def train_failure_model(
    features: pd.DataFrame,
    target: pd.Series,
) -> RandomForestClassifier:
    model = RandomForestClassifier(
        n_estimators=250,
        class_weight="balanced",
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    model.fit(features, target)
    return model


def predict_failures(
    model: RandomForestClassifier,
    features: pd.DataFrame,
    threshold: float = 0.5,
) -> pd.DataFrame:
    probabilities = model.predict_proba(features)[:, 1]
    predictions = (probabilities >= threshold).astype(int)
    return pd.DataFrame(
        {
            "failure_probability": probabilities,
            "prediction": predictions,
        },
        index=features.index,
    )


def format_failure_output(probability: float, prediction: int) -> dict[str, Any]:
    return {
        "failure_probability": round(float(probability), 4),
        "prediction": int(prediction),
    }


def save_failure_model(
    model: RandomForestClassifier,
    scaler: Any,
    path: Path = FAILURE_MODEL_PATH,
    feature_columns: list[str] | None = None,
    scaled_feature_columns: list[str] | None = None,
    base_feature_columns: list[str] | None = None,
    feature_config: dict[str, Any] | None = None,
    feature_defaults: dict[str, float] | None = None,
    feature_schema: list[dict[str, Any]] | None = None,
    training_metrics: dict[str, Any] | None = None,
) -> None:
    bundle = {
        "model": model,
        "scaler": scaler,
        "feature_columns": feature_columns or FEATURE_COLUMNS,
        "scaled_feature_columns": scaled_feature_columns or feature_columns or FEATURE_COLUMNS,
        "base_feature_columns": base_feature_columns or [],
        "feature_config": feature_config or {},
        "feature_defaults": feature_defaults or {},
        "feature_schema": feature_schema or [],
        "training_metrics": training_metrics or {},
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
    fitted_model = train_failure_model(split.X_train, split.y_train)
    results = predict_failures(fitted_model, split.X_test)
    print(results.head())
