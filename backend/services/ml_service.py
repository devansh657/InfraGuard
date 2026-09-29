from __future__ import annotations

from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Any, Protocol, TypedDict, cast

import joblib
import numpy as np
import pandas as pd

from backend.schemas.request_models import MetricsRequest
from backend.schemas.response_models import (
    AnalysisResponse,
    AnomalyResponse,
    ExplanationFeature,
    FailurePredictionResponse,
)
from backend.utils.logger import get_logger
from backend.utils.preprocessing import build_model_features, _Scaler
from backend.services.metrics_service import runtime_metrics


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ANOMALY_MODEL_PATH = PROJECT_ROOT / "ml_engine" / "models" / "anomaly_model.pkl"
FAILURE_MODEL_PATH = PROJECT_ROOT / "ml_engine" / "models" / "failure_model.pkl"

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Structural protocols for sklearn estimators.
# These describe only the subset of the sklearn API this service calls,
# avoiding a hard dependency on sklearn's (optional) type stubs.
# ---------------------------------------------------------------------------

class _FailureModel(Protocol):
    """A fitted binary classifier that exposes ``predict_proba``."""

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray: ...


class _AnomalyModel(Protocol):
    """A fitted anomaly detector that exposes ``decision_function`` and ``predict``."""

    def decision_function(self, X: pd.DataFrame) -> np.ndarray: ...
    def predict(self, X: pd.DataFrame) -> np.ndarray: ...


# ---------------------------------------------------------------------------
# Typed bundle structures (what joblib.load() returns for each model file).
# ---------------------------------------------------------------------------

class _FailureBundle(TypedDict):
    model: _FailureModel
    scaler: _Scaler
    feature_columns: list[str]
    scaled_feature_columns: list[str]
    base_feature_columns: list[str]
    feature_config: dict[str, Any]
    feature_defaults: dict[str, float | int]
    feature_schema: list[dict[str, Any]]
    training_metrics: dict[str, Any]


class _AnomalyBundle(TypedDict):
    model: _AnomalyModel
    scaler: _Scaler
    feature_columns: list[str]
    scaled_feature_columns: list[str]
    base_feature_columns: list[str]
    feature_config: dict[str, Any]
    feature_defaults: dict[str, float | int]
    feature_schema: list[dict[str, Any]]
    score_min: float
    score_max: float


# ---------------------------------------------------------------------------
# MLService
# ---------------------------------------------------------------------------

class MLService:
    def __init__(
        self,
        anomaly_model_path: Path = ANOMALY_MODEL_PATH,
        failure_model_path: Path = FAILURE_MODEL_PATH,
    ) -> None:
        self.anomaly_model_path = anomaly_model_path
        self.failure_model_path = failure_model_path
        self._anomaly_bundle: _AnomalyBundle | None = None
        self._failure_bundle: _FailureBundle | None = None

    def load_models(self) -> None:
        if self._anomaly_bundle is not None and self._failure_bundle is not None:
            return

        if not self.anomaly_model_path.exists():
            raise FileNotFoundError(f"Missing anomaly model: {self.anomaly_model_path}")
        if not self.failure_model_path.exists():
            raise FileNotFoundError(f"Missing failure model: {self.failure_model_path}")

        # joblib.load() returns Any; cast to our TypedDicts so all downstream
        # attribute access is fully type-checked from this point onwards.
        self._anomaly_bundle = cast(_AnomalyBundle, joblib.load(self.anomaly_model_path))
        self._failure_bundle = cast(_FailureBundle, joblib.load(self.failure_model_path))
        logger.info("ML models loaded")

    def predict_failure(self, metrics: MetricsRequest) -> FailurePredictionResponse:
        start = perf_counter()
        bundle = self._require_failure_bundle()
        _validate_metrics_against_schema(metrics, bundle["feature_schema"])
        features = build_model_features(
            metrics,
            scaler=bundle["scaler"],
            feature_columns=bundle["feature_columns"],
            scaled_feature_columns=bundle["scaled_feature_columns"],
            feature_config=bundle["feature_config"],
        )
        # predict_proba returns a 2-D ndarray: rows=samples, cols=class probabilities.
        probability = float(bundle["model"].predict_proba(features)[0, 1])
        prediction = int(probability >= 0.5)
        response = FailurePredictionResponse(
            failure_probability=round(probability, 4),
            prediction=prediction,
            explanation=_build_explanation(bundle["model"], features, bundle["feature_columns"]),
        )
        runtime_metrics.record_prediction((perf_counter() - start) * 1000)
        return response

    def detect_anomaly(self, metrics: MetricsRequest) -> AnomalyResponse:
        bundle = self._require_anomaly_bundle()
        _validate_metrics_against_schema(metrics, bundle["feature_schema"])
        features = build_model_features(
            metrics,
            scaler=bundle["scaler"],
            feature_columns=bundle["feature_columns"],
            scaled_feature_columns=bundle["scaled_feature_columns"],
            feature_config=bundle["feature_config"],
        )
        # decision_function returns a 1-D ndarray; negate so higher = more anomalous.
        raw_score = float(-bundle["model"].decision_function(features)[0])
        score = _normalize_score(
            raw_score,
            score_min=bundle["score_min"],
            score_max=bundle["score_max"],
        )
        # IsolationForest returns -1 for anomalies, +1 for inliers.
        is_anomaly = bool(bundle["model"].predict(features)[0] == -1)
        return AnomalyResponse(is_anomaly=is_anomaly, score=round(score, 4))

    def analyze_metrics(self, metrics: MetricsRequest) -> AnalysisResponse:
        return AnalysisResponse(
            failure=self.predict_failure(metrics),
            anomaly=self.detect_anomaly(metrics),
        )

    def models_loaded(self) -> bool:
        return self._anomaly_bundle is not None and self._failure_bundle is not None

    def model_info(self) -> dict[str, Any]:
        bundle = self._require_failure_bundle()
        return {
            "target_column": "protected_risk_label",
            "base_feature_columns": bundle["base_feature_columns"],
            "feature_columns": bundle["feature_columns"],
            "feature_defaults": bundle["feature_defaults"],
            "feature_schema": bundle["feature_schema"],
            "feature_config": bundle["feature_config"],
            "failure_metrics": bundle.get("training_metrics", {}),
        }

    def _require_anomaly_bundle(self) -> _AnomalyBundle:
        if self._anomaly_bundle is None:
            self.load_models()
        if self._anomaly_bundle is None:
            raise RuntimeError("Anomaly model failed to load.")
        return self._anomaly_bundle

    def _require_failure_bundle(self) -> _FailureBundle:
        if self._failure_bundle is None:
            self.load_models()
        if self._failure_bundle is None:
            raise RuntimeError("Failure model failed to load.")
        return self._failure_bundle


def _normalize_score(raw_score: float, score_min: float, score_max: float) -> float:
    if score_max <= score_min:
        return 0.0
    return float(np.clip((raw_score - score_min) / (score_max - score_min), 0.0, 1.0))


def _validate_metrics_against_schema(
    metrics: MetricsRequest,
    feature_schema: list[dict[str, Any]],
) -> None:
    values = metrics.to_feature_dict()
    errors: list[str] = []

    for item in feature_schema:
        name = item["name"]
        if name not in values:
            continue
        value = float(values[name])
        minimum = float(item["min"])
        maximum = float(item["max"])
        if value < minimum or value > maximum:
            errors.append(f"{name} must be between {minimum:g} and {maximum:g}")

    if errors:
        raise ValueError("Input outside trained dataset range: " + "; ".join(errors))


def _build_explanation(
    model: _FailureModel,
    features: pd.DataFrame,
    feature_columns: list[str],
    top_n: int = 5,
) -> list[ExplanationFeature]:
    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        return []

    values = np.abs(features.iloc[0].to_numpy(dtype=float))
    weighted = np.asarray(importances, dtype=float) * values
    total = float(weighted.sum())
    if total <= 0:
        weighted = np.asarray(importances, dtype=float)
        total = float(weighted.sum())
    if total <= 0:
        return []

    top_indices = np.argsort(weighted)[::-1][:top_n]
    return [
        ExplanationFeature(
            feature=feature_columns[index],
            contribution=round(float(weighted[index] / total), 4),
        )
        for index in top_indices
    ]


_service: MLService | None = None
_service_lock = Lock()


def get_ml_service() -> MLService:
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = MLService()
                _service.load_models()
    return _service
