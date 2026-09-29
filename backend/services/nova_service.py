from __future__ import annotations

from backend.schemas.response_models import NovaBriefingResponse, NovaPanelResponse
from backend.services.data_service import generate_incident_report, get_prediction_history
from backend.services.db_service import check_database
from backend.services.live_replay_service import get_live_replay_service
from backend.services.ml_service import get_ml_service


def build_nova_briefing() -> NovaBriefingResponse:
    report = generate_incident_report()
    history = get_prediction_history(limit=12)
    latest = history[0] if history else None
    models_loaded = get_ml_service().models_loaded()
    db_connected = check_database()
    live_status = _safe_live_status()

    latest_risk = latest.failure_probability if latest else 0.0
    latest_anomaly = bool(latest.is_anomaly) if latest else False
    latest_prediction = int(latest.failure_prediction) if latest else 0
    operational_state = _operational_state(models_loaded, db_connected, report.risk_level)
    urgent_alerts = _urgent_alerts(report.risk_level, latest_risk, latest_anomaly, latest_prediction)
    recommended_actions = _recommended_actions(report.risk_level, latest_risk, latest_anomaly)

    return NovaBriefingResponse(
        assistant="NOVA",
        operational_state=operational_state,
        risk_level=report.risk_level,
        spoken_briefing=_spoken_briefing(
            operational_state=operational_state,
            risk_level=report.risk_level,
            latest_risk=latest_risk,
            anomalies=report.anomalies,
            failures=report.failures,
            total=report.total_requests,
            live_rows=live_status.get("rows", 0),
        ),
        urgent_alerts=urgent_alerts,
        recommended_actions=recommended_actions,
        system_panels=[
            NovaPanelResponse(
                label="Runtime",
                value="Online" if models_loaded and db_connected else "Degraded",
                status="safe" if models_loaded and db_connected else "warning",
            ),
            NovaPanelResponse(
                label="Risk Level",
                value=report.risk_level,
                status=_risk_status(report.risk_level),
            ),
            NovaPanelResponse(
                label="Latest Risk",
                value=f"{round(latest_risk * 100)}%",
                status=_score_status(latest_risk),
            ),
            NovaPanelResponse(
                label="Stored Events",
                value=str(report.total_requests),
                status="safe" if report.total_requests else "warning",
            ),
            NovaPanelResponse(
                label="Replay Queue",
                value=f"{live_status.get('next_record_index', 0)} / {live_status.get('rows', 0)}",
                status="safe",
            ),
        ],
        command_suggestions=[
            "NOVA, give me a risk report",
            "NOVA, open live monitor",
            "NOVA, open AI analyst",
            "NOVA, scan the system",
            "NOVA, show insights",
        ],
    )


def _safe_live_status() -> dict[str, object]:
    try:
        return get_live_replay_service().status()
    except (FileNotFoundError, ValueError):
        return {"rows": 0, "next_record_index": 0, "mode": "unavailable"}


def _operational_state(models_loaded: bool, db_connected: bool, risk_level: str) -> str:
    if not models_loaded or not db_connected:
        return "DEGRADED"
    if risk_level == "HIGH":
        return "WATCH"
    return "OPERATIONAL"


def _spoken_briefing(
    operational_state: str,
    risk_level: str,
    latest_risk: float,
    anomalies: int,
    failures: int,
    total: int,
    live_rows: object,
) -> str:
    if total == 0:
        return (
            "NOVA online. InfraGuard is operational, but there are no stored events yet. "
            "Start live monitoring or run an analyst scan to generate telemetry decisions."
        )

    return (
        f"NOVA online. InfraGuard state is {operational_state}. "
        f"Current platform risk is {risk_level}. Latest AI risk is {round(latest_risk * 100)} percent. "
        f"I am tracking {total} stored decisions, including {anomalies} anomalies and {failures} elevated-risk events. "
        f"The protected replay stream has {live_rows} samples available for monitoring."
    )


def _urgent_alerts(
    risk_level: str,
    latest_risk: float,
    latest_anomaly: bool,
    latest_prediction: int,
) -> list[str]:
    alerts: list[str] = []
    if risk_level == "HIGH" or latest_risk >= 0.7:
        alerts.append("Elevated platform risk requires analyst review.")
    if latest_prediction:
        alerts.append("Latest supervised model decision indicates elevated risk.")
    if latest_anomaly:
        alerts.append("Latest anomaly engine result is outside the learned operating envelope.")
    if not alerts:
        alerts.append("No urgent incidents are active in the latest briefing.")
    return alerts


def _recommended_actions(risk_level: str, latest_risk: float, latest_anomaly: bool) -> list[str]:
    actions = ["Keep live monitoring active and review trend changes before taking action."]
    if risk_level == "HIGH" or latest_risk >= 0.7:
        actions.insert(0, "Open AI Analyst and review root cause, confidence, and playbook steps.")
        actions.append("Compare a mitigation scenario in What-If mode before making changes.")
    elif latest_anomaly:
        actions.insert(0, "Inspect anomaly markers and compare against recent telemetry history.")
    else:
        actions.append("Use NOVA voice commands to navigate, scan, or generate a risk briefing.")
    return actions[:4]


def _risk_status(risk_level: str) -> str:
    if risk_level == "HIGH":
        return "critical"
    if risk_level == "MEDIUM":
        return "warning"
    return "safe"


def _score_status(score: float) -> str:
    if score >= 0.7:
        return "critical"
    if score >= 0.35:
        return "warning"
    return "safe"
