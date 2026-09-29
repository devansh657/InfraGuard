"""End-to-end training pipeline for InfraGuard AI models."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

os.environ["LOKY_MAX_CPU_COUNT"] = "1"

try:
    from .anomaly_model import get_anomaly_score_bounds, save_anomaly_model, train_anomaly_model
    from .benchmark import benchmark_models
    from .dataset_loader import load_dataset
    from .eda import build_feature_defaults, build_feature_schema, generate_eda_artifacts
    from .evaluate import evaluate_anomaly_model, evaluate_failure_model, print_training_report
    from .failure_model import save_failure_model, train_failure_model
    from .feature_engineering import add_time_series_features, infer_feature_config
    from .preprocess import clean_dataset, scale_feature_splits, split_records
    from .utils import (
        ANOMALY_MODEL_PATH,
        BASE_NUMERIC_FEATURES,
        DEFAULT_DATASET_PATH,
        FEATURE_DESCRIPTIONS,
        FAILURE_MODEL_PATH,
        FEATURE_COLUMNS,
        MODEL_METADATA_PATH,
        RANDOM_STATE,
        REPORTS_DIR,
        SCALED_FEATURE_COLUMNS,
        TARGET_COLUMN,
        ensure_models_dir,
    )
except ImportError:
    from anomaly_model import get_anomaly_score_bounds, save_anomaly_model, train_anomaly_model
    from benchmark import benchmark_models
    from dataset_loader import load_dataset
    from eda import build_feature_defaults, build_feature_schema, generate_eda_artifacts
    from evaluate import evaluate_anomaly_model, evaluate_failure_model, print_training_report
    from failure_model import save_failure_model, train_failure_model
    from feature_engineering import add_time_series_features, infer_feature_config
    from preprocess import clean_dataset, scale_feature_splits, split_records
    from utils import (
        ANOMALY_MODEL_PATH,
        BASE_NUMERIC_FEATURES,
        DEFAULT_DATASET_PATH,
        FEATURE_DESCRIPTIONS,
        FAILURE_MODEL_PATH,
        FEATURE_COLUMNS,
        MODEL_METADATA_PATH,
        RANDOM_STATE,
        REPORTS_DIR,
        SCALED_FEATURE_COLUMNS,
        TARGET_COLUMN,
        ensure_models_dir,
    )

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train InfraGuard AI ML models.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to the network security dataset CSV.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of records reserved for evaluation.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=RANDOM_STATE,
        help="Random state for reproducible train/test splitting.",
    )
    parser.add_argument(
        "--skip-eda",
        action="store_true",
        help="Train models without regenerating EDA chart artifacts.",
    )
    parser.add_argument(
        "--skip-benchmark",
        action="store_true",
        help="Train models without regenerating model-comparison artifacts.",
    )
    return parser.parse_args()


def run_training(
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
    test_size: float = 0.2,
    random_state: int = RANDOM_STATE,
    generate_eda: bool = True,
    generate_benchmark: bool = True,
) -> dict[str, object]:
    raw_data = load_dataset(dataset_path)
    clean_data = clean_dataset(raw_data)
    train_clean, test_clean = split_records(
        clean_data,
        test_size=test_size,
        random_state=random_state,
    )
    feature_config = infer_feature_config(train_clean)
    feature_defaults = build_feature_defaults(train_clean, BASE_NUMERIC_FEATURES)
    feature_schema = build_feature_schema(clean_data, FEATURE_DESCRIPTIONS, BASE_NUMERIC_FEATURES)
    train_featured = add_time_series_features(train_clean, feature_config=feature_config)
    test_featured = add_time_series_features(test_clean, feature_config=feature_config)
    featured_data = (
        pd.concat([train_featured, test_featured], ignore_index=True)
        .sort_values("record_index")
        .reset_index(drop=True)
    )
    split = scale_feature_splits(train_featured, test_featured)

    anomaly_model = train_anomaly_model(split.X_train)
    failure_model = train_failure_model(split.X_train, split.y_train)

    score_min, score_max = get_anomaly_score_bounds(anomaly_model, split.X_train)

    failure_metrics = evaluate_failure_model(failure_model, split.X_test, split.y_test)
    anomaly_metrics = evaluate_anomaly_model(
        anomaly_model,
        split.X_test,
        score_min=score_min,
        score_max=score_max,
    )

    ensure_models_dir()
    save_anomaly_model(
        anomaly_model,
        scaler=split.scaler,
        path=ANOMALY_MODEL_PATH,
        feature_columns=FEATURE_COLUMNS,
        scaled_feature_columns=SCALED_FEATURE_COLUMNS,
        base_feature_columns=BASE_NUMERIC_FEATURES,
        feature_config=feature_config,
        feature_defaults=feature_defaults,
        feature_schema=feature_schema,
        score_reference_features=split.X_train,
    )
    save_failure_model(
        failure_model,
        scaler=split.scaler,
        path=FAILURE_MODEL_PATH,
        feature_columns=FEATURE_COLUMNS,
        scaled_feature_columns=SCALED_FEATURE_COLUMNS,
        base_feature_columns=BASE_NUMERIC_FEATURES,
        feature_config=feature_config,
        feature_defaults=feature_defaults,
        feature_schema=feature_schema,
        training_metrics=_compact_metrics(failure_metrics),
    )

    eda_report: dict[str, Any] | None = None
    if generate_eda:
        eda_report = generate_eda_artifacts(
            raw_data=raw_data,
            clean_data=clean_data,
            featured_data=featured_data,
            X_test=split.X_test,
            y_test=split.y_test,
            failure_model=failure_model,
            anomaly_model=anomaly_model,
            failure_metrics=failure_metrics,
            anomaly_metrics=anomaly_metrics,
            feature_columns=FEATURE_COLUMNS,
            score_min=score_min,
            score_max=score_max,
        )

    benchmark_report: dict[str, Any] | None = None
    if generate_benchmark:
        benchmark_report = benchmark_models(
            X_train=split.X_train,
            y_train=split.y_train,
            X_test=split.X_test,
            y_test=split.y_test,
            featured_data=featured_data,
            feature_columns=FEATURE_COLUMNS,
        )

    metadata = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_path": _public_path(Path(dataset_path)),
        "rows_loaded": len(raw_data),
        "rows_after_cleaning": len(clean_data),
        "target_column": TARGET_COLUMN,
        "base_feature_columns": BASE_NUMERIC_FEATURES,
        "feature_columns": FEATURE_COLUMNS,
        "scaled_feature_columns": SCALED_FEATURE_COLUMNS,
        "feature_config": feature_config,
        "feature_defaults": feature_defaults,
        "feature_schema": feature_schema,
        "failure_metrics": _compact_metrics(failure_metrics),
        "anomaly_metrics": anomaly_metrics,
        "eda_report_path": _public_path(REPORTS_DIR / "eda_report.md") if eda_report else "",
        "benchmark_report_path": _public_path(REPORTS_DIR / "model_benchmark.md") if benchmark_report else "",
        "best_benchmark_model": benchmark_report["best_model"] if benchmark_report else "",
    }
    MODEL_METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    return {
        "rows_loaded": len(raw_data),
        "rows_after_cleaning": len(clean_data),
        "train_rows": len(split.X_train),
        "test_rows": len(split.X_test),
        "failure_metrics": failure_metrics,
        "anomaly_metrics": anomaly_metrics,
        "anomaly_model_path": str(ANOMALY_MODEL_PATH),
        "failure_model_path": str(FAILURE_MODEL_PATH),
        "metadata_path": str(MODEL_METADATA_PATH),
        "eda_report_path": _public_path(REPORTS_DIR / "eda_report.md") if eda_report else "",
        "benchmark_report_path": _public_path(REPORTS_DIR / "model_benchmark.md") if benchmark_report else "",
    }


def _compact_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in metrics.items()
        if key not in {"roc_curve", "precision_recall_curve"}
    }


def _public_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path(__file__).resolve().parents[1]).as_posix()
    except ValueError:
        return path.name


def main() -> None:
    args = parse_args()
    results = run_training(
        dataset_path=args.dataset,
        test_size=args.test_size,
        random_state=args.random_state,
        generate_eda=not args.skip_eda,
        generate_benchmark=not args.skip_benchmark,
    )

    print(f"Rows loaded: {results['rows_loaded']}")
    print(f"Rows after cleaning: {results['rows_after_cleaning']}")
    print(f"Train rows: {results['train_rows']}")
    print(f"Test rows: {results['test_rows']}")
    print_training_report(results["failure_metrics"], results["anomaly_metrics"])
    print(f"\nSaved anomaly model: {results['anomaly_model_path']}")
    print(f"Saved failure model: {results['failure_model_path']}")
    print(f"Saved metadata: {results['metadata_path']}")
    if results["eda_report_path"]:
        print("Saved EDA artifacts under docs/eda")
    if results["benchmark_report_path"]:
        print(f"Saved model benchmark: {results['benchmark_report_path']}")


if __name__ == "__main__":
    main()
