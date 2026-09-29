from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select

from backend.database.connection import database_connected, get_session
from backend.database.tables import IncidentRecord, MetricRecord, PredictionRecord, create_tables
from backend.schemas.request_models import MetricsRequest
from backend.schemas.response_models import AnomalyResponse, FailurePredictionResponse


def initialize_database() -> None:
    create_tables()


def check_database() -> bool:
    return database_connected()


def insert_prediction(
    metrics: MetricsRequest,
    failure: FailurePredictionResponse,
    anomaly: AnomalyResponse,
) -> int:
    timestamp = datetime.now(timezone.utc)
    feature_payload = metrics.to_feature_dict()
    primary = metrics.primary_metrics()
    with get_session() as session:
        metric_record = MetricRecord(
            timestamp=timestamp,
            features_json=feature_payload,
            **primary,
        )
        session.add(metric_record)
        session.flush()
        if metric_record.id is None:
            raise RuntimeError("Database did not return a primary key for MetricRecord after flush.")

        prediction = PredictionRecord(
            metric_id=metric_record.id,
            timestamp=timestamp,
            features_json=feature_payload,
            **primary,
            failure_probability=failure.failure_probability,
            failure_prediction=failure.prediction,
            anomaly_score=anomaly.score,
            is_anomaly=anomaly.is_anomaly,
        )
        session.add(prediction)
        session.flush()
        if prediction.id is None:
            raise RuntimeError("Database did not return a primary key for PredictionRecord after flush.")

        if failure.prediction or anomaly.is_anomaly:
            session.add(
                IncidentRecord(
                    timestamp=timestamp,
                    severity="CRITICAL" if failure.prediction else "WARNING",
                    root_cause=_root_cause(metrics, failure, anomaly),
                )
            )

        return int(prediction.id)


def fetch_recent_predictions(limit: int = 100) -> list[dict[str, Any]]:
    with get_session() as session:
        rows = session.scalars(
            select(PredictionRecord).order_by(PredictionRecord.id.desc()).limit(limit)
        ).all()

    records: list[dict[str, Any]] = []
    for row in rows:
        records.append(
            {
                "id": row.id,
                "timestamp": row.timestamp.isoformat(),
                "features": row.features_json,
                "packet_size": row.packet_size,
                "transmission_rate": row.transmission_rate,
                "latency": row.latency,
                "protocol_type": row.protocol_type,
                "active_connections": row.active_connections,
                "cpu_usage": row.cpu_usage,
                "memory_usage": row.memory_usage,
                "bandwidth_utilization": row.bandwidth_utilization,
                "request_response_time": row.request_response_time,
                "auth_failures": row.auth_failures,
                "access_violations": row.access_violations,
                "firewall_blocks": row.firewall_blocks,
                "ids_alerts": row.ids_alerts,
                "failure_probability": row.failure_probability,
                "failure_prediction": row.failure_prediction,
                "anomaly_score": row.anomaly_score,
                "is_anomaly": bool(row.is_anomaly),
            }
        )
    return records


def fetch_report_counts() -> dict[str, int]:
    with get_session() as session:
        total = session.scalar(select(func.count(PredictionRecord.id))) or 0
        anomalies = session.scalar(
            select(func.count(PredictionRecord.id)).where(PredictionRecord.is_anomaly.is_(True))
        ) or 0
        failures = session.scalar(
            select(func.count(PredictionRecord.id)).where(PredictionRecord.failure_prediction == 1)
        ) or 0

    return {
        "total_requests": int(total),
        "anomalies": int(anomalies),
        "failures": int(failures),
    }


def _root_cause(
    metrics: MetricsRequest,
    failure: FailurePredictionResponse,
    anomaly: AnomalyResponse,
) -> str:
    contributors: list[str] = []
    if metrics.cpu_usage >= 80:
        contributors.append("high CPU usage")
    if metrics.bandwidth_utilization >= 90:
        contributors.append("bandwidth pressure")
    if metrics.auth_failures > 0:
        contributors.append("authentication failures")
    if metrics.access_violations > 0:
        contributors.append("access violations")
    if metrics.firewall_blocks > 0:
        contributors.append("firewall blocks")
    if metrics.ids_alerts > 0:
        contributors.append("IDS alerts")
    if failure.prediction:
        contributors.append("failure model threshold exceeded")
    if anomaly.is_anomaly:
        contributors.append("isolation forest anomaly")
    return ", ".join(contributors) or "model risk signal"
