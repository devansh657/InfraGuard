"""Research-grade model benchmarking for InfraGuard AI."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

os.environ["LOKY_MAX_CPU_COUNT"] = "1"

from sklearn.ensemble import (
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_validate

try:
    from .utils import RANDOM_STATE, REPORTS_DIR, TARGET_COLUMN, ensure_reports_dir
except ImportError:
    from utils import RANDOM_STATE, REPORTS_DIR, TARGET_COLUMN, ensure_reports_dir


def build_candidate_models() -> dict[str, Any]:
    return {
        "Logistic Regression": LogisticRegression(
            class_weight="balanced",
            max_iter=2000,
            random_state=RANDOM_STATE,
            solver="liblinear",
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=250,
            class_weight="balanced",
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=1,
        ),
        "Extra Trees": ExtraTreesClassifier(
            n_estimators=250,
            class_weight="balanced",
            min_samples_leaf=2,
            random_state=RANDOM_STATE,
            n_jobs=1,
        ),
        "Gradient Boosting": GradientBoostingClassifier(random_state=RANDOM_STATE),
        "Hist Gradient Boosting": HistGradientBoostingClassifier(random_state=RANDOM_STATE),
    }


def benchmark_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    featured_data: pd.DataFrame,
    feature_columns: list[str],
    output_dir: Path = REPORTS_DIR,
) -> dict[str, Any]:
    output_dir = ensure_reports_dir() if output_dir == REPORTS_DIR else output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    scoring = {
        "accuracy": "accuracy",
        "precision": "precision",
        "recall": "recall",
        "f1": "f1",
        "roc_auc": "roc_auc",
        "average_precision": "average_precision",
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    model_results: list[dict[str, Any]] = []
    roc_curves: dict[str, dict[str, list[float]]] = {}

    for name, estimator in build_candidate_models().items():
        cv_scores = cross_validate(
            estimator,
            X_train,
            y_train,
            cv=cv,
            scoring=scoring,
            n_jobs=1,
            error_score="raise",
        )
        estimator.fit(X_train, y_train)
        probabilities = _positive_class_scores(estimator, X_test)
        predictions = (probabilities >= 0.5).astype(int)
        fpr, tpr, thresholds = roc_curve(y_test, probabilities)
        roc_curves[name] = {
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist(),
            "thresholds": thresholds.tolist(),
        }

        model_results.append(
            {
                "model": name,
                "cross_validation": {
                    metric.replace("test_", ""): {
                        "mean": float(np.mean(values)),
                        "std": float(np.std(values)),
                    }
                    for metric, values in cv_scores.items()
                    if metric.startswith("test_")
                },
                "holdout": {
                    "accuracy": float(accuracy_score(y_test, predictions)),
                    "precision": float(precision_score(y_test, predictions, zero_division=0)),
                    "recall": float(recall_score(y_test, predictions, zero_division=0)),
                    "f1_score": float(f1_score(y_test, predictions, zero_division=0)),
                    "roc_auc": float(roc_auc_score(y_test, probabilities)),
                    "average_precision": float(average_precision_score(y_test, probabilities)),
                    "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
                },
            }
        )

    model_results = sorted(
        model_results,
        key=lambda item: (
            item["holdout"]["roc_auc"],
            item["holdout"]["recall"],
            item["holdout"]["f1_score"],
        ),
        reverse=True,
    )

    leakage_audit = build_leakage_audit(featured_data, feature_columns)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_column": TARGET_COLUMN,
        "best_model": model_results[0]["model"],
        "model_results": model_results,
        "roc_curves": roc_curves,
        "leakage_audit": leakage_audit,
        "evaluation_notes": build_evaluation_notes(model_results, leakage_audit),
    }

    _write_json(output_dir / "model_benchmark.json", report)
    _write_markdown(output_dir / "model_benchmark.md", report)
    _plot_model_comparison(model_results, output_dir / "model_comparison.png")
    _plot_roc_comparison(roc_curves, model_results, output_dir / "roc_comparison.png")
    return report


def build_leakage_audit(featured_data: pd.DataFrame, feature_columns: list[str]) -> dict[str, Any]:
    correlation_frame = featured_data[feature_columns + [TARGET_COLUMN]].corr(numeric_only=True)
    target_correlations = (
        correlation_frame[TARGET_COLUMN]
        .drop(labels=[TARGET_COLUMN])
        .abs()
        .sort_values(ascending=False)
    )
    top = target_correlations.head(10)
    return {
        "top_absolute_target_correlations": {
            feature: float(value) for feature, value in top.items()
        },
        "max_absolute_target_correlation": float(target_correlations.max()),
        "high_correlation_features": [
            feature for feature, value in target_correlations.items() if float(value) >= 0.9
        ],
    }


def build_evaluation_notes(
    model_results: list[dict[str, Any]],
    leakage_audit: dict[str, Any],
) -> list[str]:
    notes: list[str] = []
    best = model_results[0]
    if best["holdout"]["roc_auc"] >= 0.995:
        notes.append(
            "Holdout ROC AUC is near-perfect; project documentation should discuss dataset separability, synthetic generation risk, and possible feature leakage."
        )
    if leakage_audit["high_correlation_features"]:
        notes.append(
            "Some features have very high correlation with the target and should be discussed as potential leakage or strong proxy variables."
        )
    notes.append(
        "Use recall and PR AUC alongside ROC AUC because missed anomalies are operationally costly."
    )
    return notes


def _positive_class_scores(estimator: Any, X_test: pd.DataFrame) -> np.ndarray:
    if hasattr(estimator, "predict_proba"):
        return estimator.predict_proba(X_test)[:, 1]
    if hasattr(estimator, "decision_function"):
        scores = estimator.decision_function(X_test)
        minimum = float(np.min(scores))
        maximum = float(np.max(scores))
        if maximum <= minimum:
            return np.zeros_like(scores, dtype=float)
        return (scores - minimum) / (maximum - minimum)
    return estimator.predict(X_test)


def _plot_model_comparison(model_results: list[dict[str, Any]], path: Path) -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(path.parent / ".matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metrics = ["accuracy", "precision", "recall", "f1_score", "roc_auc", "average_precision"]
    names = [item["model"] for item in model_results]
    values = np.array([[item["holdout"][metric] for metric in metrics] for item in model_results])

    fig, ax = plt.subplots(figsize=(12, 6.5))
    width = 0.12
    positions = np.arange(len(names))
    for index, metric in enumerate(metrics):
        ax.bar(positions + (index - len(metrics) / 2) * width, values[:, index], width, label=metric)

    ax.set_title("Holdout Model Comparison")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(positions)
    ax.set_xticklabels(names, rotation=20, ha="right")
    ax.legend(ncol=3, fontsize=8)
    ax.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _plot_roc_comparison(
    roc_curves: dict[str, dict[str, list[float]]],
    model_results: list[dict[str, Any]],
    path: Path,
) -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(path.parent / ".matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    auc_by_name = {item["model"]: item["holdout"]["roc_auc"] for item in model_results}
    fig, ax = plt.subplots(figsize=(7.5, 6))
    for name, curve in roc_curves.items():
        ax.plot(curve["fpr"], curve["tpr"], linewidth=2, label=f"{name} ({auc_by_name[name]:.3f})")
    ax.plot([0, 1], [0, 1], color="#94a3b8", linestyle="--")
    ax.set_title("ROC Curve Comparison")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate / Recall")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(_json_safe(payload), indent=2), encoding="utf-8")


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# InfraGuard AI Model Benchmark",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Target: `{report['target_column']}`",
        f"Best model by holdout ROC AUC/recall/F1: **{report['best_model']}**",
        "",
        "## Holdout Results",
        "",
        "| Model | Accuracy | Precision | Recall | F1 | ROC AUC | PR AUC |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in report["model_results"]:
        holdout = item["holdout"]
        lines.append(
            f"| {item['model']} | {holdout['accuracy']:.4f} | {holdout['precision']:.4f} | {holdout['recall']:.4f} | {holdout['f1_score']:.4f} | {holdout['roc_auc']:.4f} | {holdout['average_precision']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Leakage / Separability Audit",
            "",
            f"- Max absolute target correlation: `{report['leakage_audit']['max_absolute_target_correlation']:.4f}`",
            f"- High-correlation features: `{report['leakage_audit']['high_correlation_features']}`",
            "",
            "## Research Notes",
            "",
        ]
    )
    lines.extend([f"- {note}" for note in report["evaluation_notes"]])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if pd.isna(value):
        return None
    return value
