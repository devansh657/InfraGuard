from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.schemas.request_models import MetricsRequest
from backend.schemas.response_models import (
    AnalystResponse,
    DriftResponse,
    RootCauseResponse,
    WhatIfResponse,
)
from backend.services.ml_service import MLService, get_ml_service


FEATURE_CATEGORIES = {
    "Packet_Size": "Network flow",
    "Transmission_Rate": "Network flow",
    "Latency": "Network flow",
    "Protocol_Type": "Network flow",
    "Active_Connections": "Network flow",
    "CPU_Usage": "System pressure",
    "Memory_Usage": "System pressure",
    "Bandwidth_Utilization": "System pressure",
    "Request_Response_Time": "System pressure",
    "Auth_Failures": "Security signal",
    "Access_Violations": "Security signal",
    "Firewall_Blocks": "Security signal",
    "IDS_Alerts": "Security signal",
}

SENSITIVE_SECURITY_FEATURES = {
    "Auth_Failures",
    "Access_Violations",
    "Firewall_Blocks",
    "IDS_Alerts",
}

PRESSURE_FEATURES = {
    "CPU_Usage",
    "Memory_Usage",
    "Bandwidth_Utilization",
    "Latency",
    "Request_Response_Time",
    "Active_Connections",
}


@dataclass(frozen=True)
class FeatureWindow:
    minimum: float
    maximum: float
    median: float


def analyze_telemetry(
    metrics: MetricsRequest,
    ml_service: MLService | None = None,
) -> AnalystResponse:
    service = ml_service or get_ml_service()
    analysis = service.analyze_metrics(metrics)
    schema = service.model_info().get("feature_schema", [])
    values = metrics.to_feature_dict()

    severity = _severity(
        failure_probability=analysis.failure.failure_probability,
        anomaly_score=analysis.anomaly.score,
        is_anomaly=analysis.anomaly.is_anomaly,
    )
    priority_score = _priority_score(
        failure_probability=analysis.failure.failure_probability,
        anomaly_score=analysis.anomaly.score,
        is_anomaly=analysis.anomaly.is_anomaly,
    )
    drift = _detect_drift(values, schema)
    root_causes = _root_causes(analysis.failure.explanation, values, schema, drift)
    recommendations = _recommendations(severity, root_causes, drift)
    playbook = _playbook(severity, root_causes, drift)
    confidence = _confidence(
        failure_probability=analysis.failure.failure_probability,
        is_anomaly=analysis.anomaly.is_anomaly,
        root_causes=root_causes,
        drift=drift,
    )

    return AnalystResponse(
        analysis=analysis,
        severity=severity,
        priority_score=priority_score,
        confidence=confidence,
        root_causes=root_causes,
        recommendations=recommendations,
        playbook=playbook,
        incident_summary=_incident_summary(
            severity=severity,
            risk=analysis.failure.failure_probability,
            is_anomaly=analysis.anomaly.is_anomaly,
            root_causes=root_causes,
            drift=drift,
        ),
        drift=drift,
    )


def compare_what_if(
    baseline: MetricsRequest,
    candidate: MetricsRequest,
    ml_service: MLService | None = None,
) -> WhatIfResponse:
    service = ml_service or get_ml_service()
    baseline_result = analyze_telemetry(baseline, service)
    candidate_result = analyze_telemetry(candidate, service)
    baseline_risk = baseline_result.analysis.failure.failure_probability
    candidate_risk = candidate_result.analysis.failure.failure_probability
    risk_delta = round(candidate_risk - baseline_risk, 4)
    priority_delta = candidate_result.priority_score - baseline_result.priority_score

    if abs(risk_delta) < 0.01:
        impact = "The proposed change has minimal impact on the model risk score."
    elif risk_delta < 0:
        impact = (
            f"The proposed change reduces predicted risk by {abs(round(risk_delta * 100, 1))}% "
            f"and shifts priority by {priority_delta} points."
        )
    else:
        impact = (
            f"The proposed change increases predicted risk by {round(risk_delta * 100, 1)}% "
            f"and shifts priority by +{priority_delta} points."
        )

    return WhatIfResponse(
        baseline=baseline_result,
        candidate=candidate_result,
        risk_delta=risk_delta,
        priority_delta=priority_delta,
        severity_change=f"{baseline_result.severity} -> {candidate_result.severity}",
        impact_summary=impact,
    )


def _severity(failure_probability: float, anomaly_score: float, is_anomaly: bool) -> str:
    if failure_probability >= 0.85 or (failure_probability >= 0.7 and is_anomaly):
        return "CRITICAL"
    if failure_probability >= 0.6 or (failure_probability >= 0.45 and anomaly_score >= 0.7):
        return "HIGH"
    if failure_probability >= 0.32 or is_anomaly or anomaly_score >= 0.55:
        return "MEDIUM"
    return "LOW"


def _priority_score(failure_probability: float, anomaly_score: float, is_anomaly: bool) -> int:
    anomaly_bonus = 0.12 if is_anomaly else 0.0
    score = (failure_probability * 0.67) + (anomaly_score * 0.21) + anomaly_bonus
    return int(max(0, min(100, round(score * 100))))


def _confidence(
    failure_probability: float,
    is_anomaly: bool,
    root_causes: list[RootCauseResponse],
    drift: DriftResponse,
) -> float:
    distance_from_boundary = abs(failure_probability - 0.5) * 2
    explanation_strength = sum(item.contribution for item in root_causes[:3])
    agreement_bonus = 0.08 if (failure_probability >= 0.5 and is_anomaly) or (failure_probability < 0.5 and not is_anomaly) else 0.0
    drift_penalty = 0.08 if drift.level == "HIGH" else 0.03 if drift.level == "MEDIUM" else 0.0
    confidence = 0.48 + (distance_from_boundary * 0.24) + (explanation_strength * 0.22) + agreement_bonus - drift_penalty
    return round(max(0.35, min(0.97, confidence)), 4)


def _root_causes(
    explanation: list[Any],
    values: dict[str, float],
    schema: list[dict[str, Any]],
    drift: DriftResponse,
) -> list[RootCauseResponse]:
    windows = _schema_windows(schema)
    causes: list[RootCauseResponse] = []

    for item in explanation[:5]:
        feature = item.feature
        contribution = float(item.contribution)
        category = _category(feature)
        value_text = _feature_evidence(feature, values, windows.get(feature))
        causes.append(
            RootCauseResponse(
                feature=feature,
                category=category,
                contribution=round(contribution, 4),
                severity=_cause_severity(contribution, drift, feature),
                evidence=value_text,
            )
        )

    existing = {item.feature for item in causes}
    for feature in drift.shifted_features[:3]:
        if feature in existing:
            continue
        causes.append(
            RootCauseResponse(
                feature=feature,
                category=_category(feature),
                contribution=0.05,
                severity="watch",
                evidence=_feature_evidence(feature, values, windows.get(feature)),
            )
        )

    return causes[:6]


def _detect_drift(values: dict[str, float], schema: list[dict[str, Any]]) -> DriftResponse:
    scores: list[tuple[str, float]] = []
    for item in schema:
        feature = item.get("name")
        if feature not in values:
            continue
        window = FeatureWindow(
            minimum=float(item.get("min", 0.0)),
            maximum=float(item.get("max", 0.0)),
            median=float(item.get("median", item.get("mean", 0.0))),
        )
        width = max(window.maximum - window.minimum, 1e-9)
        distance = abs(values[feature] - window.median) / width
        scores.append((feature, max(0.0, min(1.0, distance * 2.0))))

    scores.sort(key=lambda pair: pair[1], reverse=True)
    top_scores = scores[:5]
    drift_score = round(sum(score for _, score in top_scores) / max(len(top_scores), 1), 4)
    shifted = [feature for feature, score in top_scores if score >= 0.55]
    level = "HIGH" if drift_score >= 0.65 else "MEDIUM" if drift_score >= 0.35 else "LOW"
    if shifted:
        summary = f"{len(shifted)} telemetry signals are far from the learned operating center."
    else:
        summary = "Current telemetry remains close to the learned operating envelope."
    return DriftResponse(
        drift_score=drift_score,
        level=level,
        shifted_features=shifted,
        summary=summary,
    )


def _recommendations(
    severity: str,
    root_causes: list[RootCauseResponse],
    drift: DriftResponse,
) -> list[str]:
    categories = {item.category for item in root_causes}
    features = {item.feature for item in root_causes}
    recommendations: list[str] = []

    if "Security signal" in categories or features & SENSITIVE_SECURITY_FEATURES:
        recommendations.extend(
            [
                "Inspect authentication failures, IDS alerts, and blocked-traffic clusters.",
                "Prioritize suspicious source patterns and temporarily tighten access controls.",
            ]
        )

    if "System pressure" in categories or features & PRESSURE_FEATURES:
        recommendations.extend(
            [
                "Check host capacity, memory pressure, and request-response saturation.",
                "Prepare a scale-out or traffic-shedding action if priority continues rising.",
            ]
        )

    if "Network flow" in categories:
        recommendations.append("Inspect gateway throughput, active connection bursts, and latency-sensitive paths.")

    if drift.level in {"MEDIUM", "HIGH"}:
        recommendations.append("Monitor for model drift and flag this sample for analyst review before retraining.")

    if severity in {"HIGH", "CRITICAL"}:
        recommendations.insert(0, "Open an incident investigation and assign an owner before automated remediation.")

    if not recommendations:
        recommendations.append("Continue monitoring; no immediate remediation is recommended for this sample.")

    return _unique(recommendations)[:6]


def _playbook(
    severity: str,
    root_causes: list[RootCauseResponse],
    drift: DriftResponse,
) -> list[str]:
    playbook = [
        "Confirm the latest telemetry sample and compare it with the previous five samples.",
        "Review the top AI root-cause drivers before changing infrastructure state.",
    ]
    if severity in {"HIGH", "CRITICAL"}:
        playbook.append("Create an incident ticket with priority, evidence, and current AI summary.")
    if any(item.category == "Security signal" for item in root_causes):
        playbook.append("Correlate IDS, firewall, and authentication events for the same time window.")
    if any(item.category == "System pressure" for item in root_causes):
        playbook.append("Validate whether scaling, queue throttling, or workload redistribution would lower risk.")
    if drift.level == "HIGH":
        playbook.append("Treat this sample as out-of-distribution and request human validation.")
    return playbook[:6]


def _incident_summary(
    severity: str,
    risk: float,
    is_anomaly: bool,
    root_causes: list[RootCauseResponse],
    drift: DriftResponse,
) -> str:
    cause_text = ", ".join(item.feature for item in root_causes[:3]) or "no dominant driver"
    anomaly_text = "an outlier pattern" if is_anomaly else "a familiar operating pattern"
    return (
        f"InfraGuard AI classifies the current sample as {severity} with "
        f"{round(risk * 100, 1)}% predicted elevated-risk probability. "
        f"The anomaly engine reports {anomaly_text}. Primary drivers are {cause_text}. "
        f"Drift status is {drift.level}: {drift.summary}"
    )


def _schema_windows(schema: list[dict[str, Any]]) -> dict[str, FeatureWindow]:
    windows: dict[str, FeatureWindow] = {}
    for item in schema:
        name = item.get("name")
        if not name:
            continue
        windows[str(name)] = FeatureWindow(
            minimum=float(item.get("min", 0.0)),
            maximum=float(item.get("max", 0.0)),
            median=float(item.get("median", item.get("mean", 0.0))),
        )
    return windows


def _feature_evidence(
    feature: str,
    values: dict[str, float],
    window: FeatureWindow | None,
) -> str:
    value = values.get(feature)
    if value is None:
        return "Derived model signal contributed strongly to this decision."
    if window is None:
        return f"Observed value is {round(value, 3)}."
    position = "above" if value > window.median else "below" if value < window.median else "near"
    return (
        f"Observed value {round(value, 3)} is {position} the learned center "
        f"of {round(window.median, 3)} within the protected training range."
    )


def _category(feature: str) -> str:
    if feature in FEATURE_CATEGORIES:
        return FEATURE_CATEGORIES[feature]
    if feature.startswith("DWT_"):
        return "Signal pattern"
    if feature.endswith("_flag") or feature.startswith("rolling_"):
        return "Engineered signal"
    return "Model signal"


def _cause_severity(contribution: float, drift: DriftResponse, feature: str) -> str:
    if contribution >= 0.28 or (drift.level == "HIGH" and feature in drift.shifted_features):
        return "critical"
    if contribution >= 0.16:
        return "high"
    if contribution >= 0.08:
        return "watch"
    return "low"


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output
