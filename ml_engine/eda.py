"""Exploratory data analysis and model evaluation chart generation."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    from .anomaly_model import predict_anomalies
    from .failure_model import predict_failures
    from .utils import REPORTS_DIR, TARGET_COLUMN, ensure_reports_dir
except ImportError:
    from anomaly_model import predict_anomalies
    from failure_model import predict_failures
    from utils import REPORTS_DIR, TARGET_COLUMN, ensure_reports_dir


PROJECT_ROOT = REPORTS_DIR.parents[1]


def generate_eda_artifacts(
    raw_data: pd.DataFrame,
    clean_data: pd.DataFrame,
    featured_data: pd.DataFrame,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    failure_model: Any,
    anomaly_model: Any,
    failure_metrics: dict[str, Any],
    anomaly_metrics: dict[str, Any],
    feature_columns: list[str],
    score_min: float,
    score_max: float,
    output_dir: Path = REPORTS_DIR,
) -> dict[str, Any]:
    """Generate dataset summaries and visual artifacts for the ML phase."""

    output_dir = ensure_reports_dir() if output_dir == REPORTS_DIR else output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = build_dataset_summary(raw_data, clean_data, featured_data, feature_columns)
    _write_json(output_dir / "dataset_summary.json", summary)

    artifacts: dict[str, str] = {}
    try:
        os.environ.setdefault("MPLCONFIGDIR", str(output_dir / ".matplotlib"))
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        summary["chart_generation_error"] = (
            "matplotlib is required to generate EDA charts. "
            "Install requirements.txt and run training again."
        )
        _write_json(output_dir / "dataset_summary.json", summary)
        raise RuntimeError(summary["chart_generation_error"]) from exc

    artifacts["label_distribution"] = _public_path(
        _plot_label_distribution(clean_data, output_dir / "label_distribution.png", plt)
    )
    artifacts["missing_values"] = _public_path(
        _plot_missing_values(raw_data, output_dir / "missing_values.png", plt)
    )
    artifacts["correlation_heatmap"] = _public_path(
        _plot_correlation_heatmap(featured_data, feature_columns, output_dir / "correlation_heatmap.png", plt)
    )
    artifacts["feature_distributions"] = _public_path(
        _plot_feature_distributions(clean_data, output_dir / "feature_distributions.png", plt)
    )
    artifacts["confusion_matrix"] = _public_path(
        _plot_confusion_matrix(failure_metrics, output_dir / "confusion_matrix.png", plt)
    )
    artifacts["roc_curve"] = _public_path(
        _plot_roc_curve(failure_metrics, output_dir / "roc_curve.png", plt)
    )
    artifacts["precision_recall_curve"] = _public_path(
        _plot_precision_recall_curve(failure_metrics, output_dir / "precision_recall_curve.png", plt)
    )
    artifacts["feature_importance"] = _public_path(
        _plot_feature_importance(
            failure_model,
            feature_columns,
            output_dir / "feature_importance.png",
            plt,
        )
    )
    artifacts["anomaly_scores"] = _public_path(
        _plot_anomaly_scores(
            anomaly_model,
            X_test,
            score_min,
            score_max,
            output_dir / "anomaly_score_distribution.png",
            plt,
        )
    )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "failure_metrics": _without_curve_arrays(failure_metrics),
        "anomaly_metrics": anomaly_metrics,
        "artifacts": artifacts,
    }
    _write_json(output_dir / "model_evaluation.json", report)
    _write_markdown_report(output_dir / "eda_report.md", report)
    return report


def build_dataset_summary(
    raw_data: pd.DataFrame,
    clean_data: pd.DataFrame,
    featured_data: pd.DataFrame,
    feature_columns: list[str],
) -> dict[str, Any]:
    label_counts = clean_data[TARGET_COLUMN].value_counts().sort_index()
    missing_values = raw_data.isna().sum().sort_values(ascending=False)
    non_constant_features = [
        column for column in feature_columns if column in featured_data and featured_data[column].nunique() > 1
    ]

    return {
        "source_rows": int(len(raw_data)),
        "clean_rows": int(len(clean_data)),
        "feature_count": int(len(feature_columns)),
        "target_column": TARGET_COLUMN,
        "label_distribution": {str(key): int(value) for key, value in label_counts.items()},
        "missing_values": {column: int(value) for column, value in missing_values.items()},
        "columns": list(raw_data.columns),
        "feature_columns": feature_columns,
        "non_constant_feature_count": len(non_constant_features),
        "describe": _json_safe(clean_data.describe().to_dict()),
    }


def build_feature_schema(
    clean_data: pd.DataFrame,
    feature_descriptions: dict[str, str],
    base_feature_columns: list[str],
) -> list[dict[str, Any]]:
    schema: list[dict[str, Any]] = []
    for column in base_feature_columns:
        series = clean_data[column]
        schema.append(
            {
                "name": column,
                "description": feature_descriptions.get(column, column.replace("_", " ")),
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "dtype": str(series.dtype),
            }
        )
    return schema


def build_feature_defaults(clean_data: pd.DataFrame, base_feature_columns: list[str]) -> dict[str, float | int]:
    defaults: dict[str, float | int] = {}
    for column in base_feature_columns:
        median = clean_data[column].median()
        if pd.api.types.is_integer_dtype(clean_data[column]):
            defaults[column] = int(round(float(median)))
        else:
            defaults[column] = float(median)
    return defaults


def _plot_label_distribution(data: pd.DataFrame, path: Path, plt: Any) -> Path:
    counts = data[TARGET_COLUMN].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(["Normal", "Anomalous"], [counts.get(0, 0), counts.get(1, 0)], color=["#34d399", "#fb7185"])
    ax.set_title("Anomalous_Load Class Distribution")
    ax.set_ylabel("Rows")
    _save(fig, path)
    return path


def _plot_missing_values(data: pd.DataFrame, path: Path, plt: Any) -> Path:
    missing = data.isna().sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(missing.index, missing.values, color="#60a5fa")
    ax.set_title("Missing Values by Column")
    ax.set_ylabel("Missing values")
    ax.tick_params(axis="x", rotation=75)
    _save(fig, path)
    return path


def _plot_correlation_heatmap(data: pd.DataFrame, feature_columns: list[str], path: Path, plt: Any) -> Path:
    columns = [column for column in feature_columns if data[column].nunique() > 1]
    corr = data[columns + [TARGET_COLUMN]].corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(12, 10))
    image = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=90, fontsize=7)
    ax.set_yticklabels(corr.columns, fontsize=7)
    ax.set_title("Feature Correlation Heatmap")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    _save(fig, path)
    return path


def _plot_feature_distributions(data: pd.DataFrame, path: Path, plt: Any) -> Path:
    columns = [
        "Packet_Size",
        "Transmission_Rate",
        "Latency",
        "Active_Connections",
        "CPU_Usage",
        "Memory_Usage",
        "Bandwidth_Utilization",
        "Request_Response_Time",
        "Auth_Failures",
        "Access_Violations",
        "Firewall_Blocks",
        "IDS_Alerts",
    ]
    fig, axes = plt.subplots(4, 3, figsize=(13, 11))
    for ax, column in zip(axes.flatten(), columns):
        ax.hist(data[column], bins=32, color="#22d3ee", alpha=0.82)
        ax.set_title(column, fontsize=10)
    _save(fig, path)
    return path


def _plot_confusion_matrix(failure_metrics: dict[str, Any], path: Path, plt: Any) -> Path:
    matrix = np.array(failure_metrics["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(5.5, 4.8))
    image = ax.imshow(matrix, cmap="Blues")
    ax.set_title("Failure Model Confusion Matrix")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_xticks([0, 1], labels=["Normal", "Anomalous"])
    ax.set_yticks([0, 1], labels=["Normal", "Anomalous"])
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, str(matrix[i, j]), ha="center", va="center", color="#111827")
    fig.colorbar(image, ax=ax)
    _save(fig, path)
    return path


def _plot_roc_curve(failure_metrics: dict[str, Any], path: Path, plt: Any) -> Path:
    curve = failure_metrics["roc_curve"]
    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.plot(curve["fpr"], curve["tpr"], color="#34d399", linewidth=2)
    ax.plot([0, 1], [0, 1], color="#94a3b8", linestyle="--")
    ax.set_title(f"ROC Curve (AUC={failure_metrics['roc_auc']:.4f})")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate / Recall")
    ax.grid(alpha=0.25)
    _save(fig, path)
    return path


def _plot_precision_recall_curve(failure_metrics: dict[str, Any], path: Path, plt: Any) -> Path:
    curve = failure_metrics["precision_recall_curve"]
    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.plot(curve["recall"], curve["precision"], color="#fbbf24", linewidth=2)
    ax.set_title(f"Precision-Recall Curve (AP={failure_metrics['average_precision']:.4f})")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.grid(alpha=0.25)
    _save(fig, path)
    return path


def _plot_feature_importance(model: Any, feature_columns: list[str], path: Path, plt: Any) -> Path:
    importances = getattr(model, "feature_importances_", np.zeros(len(feature_columns)))
    importance_frame = (
        pd.DataFrame({"feature": feature_columns, "importance": importances})
        .sort_values("importance", ascending=False)
        .head(15)
        .sort_values("importance")
    )
    fig, ax = plt.subplots(figsize=(9, 7))
    ax.barh(importance_frame["feature"], importance_frame["importance"], color="#a78bfa")
    ax.set_title("Top Random Forest Feature Importances")
    ax.set_xlabel("Importance")
    _save(fig, path)
    return path


def _plot_anomaly_scores(
    model: Any,
    X_test: pd.DataFrame,
    score_min: float,
    score_max: float,
    path: Path,
    plt: Any,
) -> Path:
    results = predict_anomalies(model, X_test, score_min=score_min, score_max=score_max)
    fig, ax = plt.subplots(figsize=(7, 4.8))
    ax.hist(results["anomaly_score"], bins=32, color="#fb7185", alpha=0.82)
    ax.set_title("Isolation Forest Anomaly Score Distribution")
    ax.set_xlabel("Normalized anomaly score")
    ax.set_ylabel("Rows")
    _save(fig, path)
    return path


def _write_markdown_report(path: Path, report: dict[str, Any]) -> None:
    failure = report["failure_metrics"]
    anomaly = report["anomaly_metrics"]
    summary = report["summary"]
    lines = [
        "# InfraGuard AI EDA Report",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Dataset",
        "",
        f"- Source rows: {summary['source_rows']}",
        f"- Clean rows: {summary['clean_rows']}",
        f"- Feature count: {summary['feature_count']}",
        f"- Target column: `{summary['target_column']}`",
        f"- Label distribution: `{summary['label_distribution']}`",
        "",
        "## Failure Model Metrics",
        "",
        f"- Accuracy: {failure['accuracy']:.4f}",
        f"- Precision: {failure['precision']:.4f}",
        f"- Recall: {failure['recall']:.4f}",
        f"- F1-score: {failure['f1_score']:.4f}",
        f"- ROC AUC: {failure['roc_auc']:.4f}",
        f"- Average precision: {failure['average_precision']:.4f}",
        f"- Confusion matrix: `{failure['confusion_matrix']}`",
        "",
        "## Anomaly Model Metrics",
        "",
        f"- Anomaly rate: {anomaly['anomaly_rate']:.4f}",
        "",
        "## Chart Artifacts",
        "",
    ]
    lines.extend([f"- {name}: `{artifact}`" for name, artifact in report["artifacts"].items()])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _without_curve_arrays(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metrics.items() if key not in {"roc_curve", "precision_recall_curve"}}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(_json_safe(payload), indent=2), encoding="utf-8")


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


def _save(fig: Any, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    fig.clf()


def _public_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.name
