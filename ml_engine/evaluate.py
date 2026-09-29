"""Evaluation helpers for InfraGuard AI models."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    precision_recall_curve,
    recall_score,
    roc_auc_score,
    roc_curve,
)

try:
    from .anomaly_model import format_anomaly_output, predict_anomalies
    from .dataset_loader import load_dataset
    from .feature_engineering import add_time_series_features
    from .failure_model import predict_failures
    from .preprocess import apply_scaler, clean_dataset, split_records
    from .utils import (
        ANOMALY_MODEL_PATH,
        FAILURE_MODEL_PATH,
        RANDOM_STATE,
        DEFAULT_DATASET_PATH,
        TARGET_COLUMN,
        load_pickle,
    )
except ImportError:
    from anomaly_model import format_anomaly_output, predict_anomalies
    from dataset_loader import load_dataset
    from feature_engineering import add_time_series_features
    from failure_model import predict_failures
    from preprocess import apply_scaler, clean_dataset, split_records
    from utils import (
        ANOMALY_MODEL_PATH,
        FAILURE_MODEL_PATH,
        RANDOM_STATE,
        DEFAULT_DATASET_PATH,
        TARGET_COLUMN,
        load_pickle,
    )


def evaluate_failure_model(model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
    predictions = predict_failures(model, X_test)
    y_pred = predictions["prediction"]
    y_score = predictions["failure_probability"]
    fpr, tpr, roc_thresholds = roc_curve(y_test, y_score)
    pr_precision, pr_recall, pr_thresholds = precision_recall_curve(y_test, y_score)

    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1_score": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_score),
        "average_precision": average_precision_score(y_test, y_score),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "roc_curve": {
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist(),
            "thresholds": roc_thresholds.tolist(),
        },
        "precision_recall_curve": {
            "precision": pr_precision.tolist(),
            "recall": pr_recall.tolist(),
            "thresholds": pr_thresholds.tolist(),
        },
    }


def evaluate_anomaly_model(
    model: Any,
    X_test: pd.DataFrame,
    score_min: float | None = None,
    score_max: float | None = None,
    sample_size: int = 5,
) -> dict[str, Any]:
    results = predict_anomalies(model, X_test, score_min=score_min, score_max=score_max)
    samples = results.sort_values("anomaly_score", ascending=False).head(sample_size)

    return {
        "anomaly_rate": float(results["anomaly_label"].mean()),
        "sample_results": [
            format_anomaly_output(row.anomaly_score, row.anomaly_label)
            for row in samples.itertuples()
        ],
    }


def print_training_report(
    failure_metrics: dict[str, Any],
    anomaly_metrics: dict[str, Any],
) -> None:
    print("\nFailure prediction metrics")
    for key in ["accuracy", "precision", "recall", "f1_score", "roc_auc", "average_precision"]:
        print(f"- {key}: {failure_metrics[key]:.4f}")
    print(f"- confusion_matrix: {failure_metrics['confusion_matrix']}")

    print("\nAnomaly detection metrics")
    print(f"- anomaly_rate: {anomaly_metrics['anomaly_rate']:.4f}")
    print(f"- sample_results: {anomaly_metrics['sample_results']}")


def evaluate_saved_models(
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
    anomaly_model_path: str | Path = ANOMALY_MODEL_PATH,
    failure_model_path: str | Path = FAILURE_MODEL_PATH,
    test_size: float = 0.2,
    random_state: int = RANDOM_STATE,
) -> dict[str, Any]:
    anomaly_bundle = load_pickle(Path(anomaly_model_path))
    failure_bundle = load_pickle(Path(failure_model_path))

    raw_data = load_dataset(dataset_path)
    _, test_clean = split_records(
        clean_dataset(raw_data),
        test_size=test_size,
        random_state=random_state,
    )
    test_frame = add_time_series_features(
        test_clean,
        feature_config=failure_bundle.get("feature_config"),
    )
    scaled_test = apply_scaler(test_frame, failure_bundle["scaler"])
    feature_columns = failure_bundle["feature_columns"]

    failure_metrics = evaluate_failure_model(
        failure_bundle["model"],
        scaled_test[feature_columns],
        scaled_test[TARGET_COLUMN],
    )
    anomaly_metrics = evaluate_anomaly_model(
        anomaly_bundle["model"],
        scaled_test[feature_columns],
        score_min=anomaly_bundle["score_min"],
        score_max=anomaly_bundle["score_max"],
    )

    return {
        "failure_metrics": failure_metrics,
        "anomaly_metrics": anomaly_metrics,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate saved InfraGuard AI models.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--anomaly-model", type=Path, default=ANOMALY_MODEL_PATH)
    parser.add_argument("--failure-model", type=Path, default=FAILURE_MODEL_PATH)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=RANDOM_STATE)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    report = evaluate_saved_models(
        dataset_path=args.dataset,
        anomaly_model_path=args.anomaly_model,
        failure_model_path=args.failure_model,
        test_size=args.test_size,
        random_state=args.random_state,
    )
    print_training_report(report["failure_metrics"], report["anomaly_metrics"])
