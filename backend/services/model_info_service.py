from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.services.ml_service import get_ml_service


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EDA_DIR = PROJECT_ROOT / "docs" / "eda"


def get_model_info_payload() -> dict[str, Any]:
    return get_ml_service().model_info()


def get_eda_payload() -> dict[str, Any]:
    summary_path = EDA_DIR / "dataset_summary.json"
    evaluation_path = EDA_DIR / "model_evaluation.json"
    if not summary_path.exists() or not evaluation_path.exists():
        return {"available": False, "summary": {}, "evaluation": {}}

    return {
        "available": True,
        "summary": _public_eda_summary(_read_json(summary_path)),
        "evaluation": _public_evaluation(_read_json(evaluation_path)),
    }


def get_benchmark_payload() -> dict[str, Any]:
    benchmark_path = EDA_DIR / "model_benchmark.json"
    if not benchmark_path.exists():
        return {"available": False, "benchmark": {}}
    return {
        "available": True,
        "benchmark": _public_benchmark(_read_json(benchmark_path)),
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _public_eda_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """Expose aggregate EDA signals without leaking internal column/target details."""
    return {
        "source_rows": summary.get("source_rows", 0),
        "clean_rows": summary.get("clean_rows", 0),
        "feature_count": summary.get("feature_count", 0),
        "label_distribution": summary.get("label_distribution", {}),
        "non_constant_feature_count": summary.get("non_constant_feature_count", 0),
    }


def _public_evaluation(evaluation: dict[str, Any]) -> dict[str, Any]:
    payload = dict(evaluation)
    payload.pop("target_column", None)
    summary = payload.get("summary")
    if isinstance(summary, dict):
        payload["summary"] = _public_eda_summary(summary)
    return payload


def _public_benchmark(benchmark: dict[str, Any]) -> dict[str, Any]:
    payload = dict(benchmark)
    payload["target_column"] = "protected_risk_label"
    return payload
