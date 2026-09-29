from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.database.connection import engine


class Base(DeclarativeBase):
    pass


class MetricRecord(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    features_json: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    packet_size: Mapped[int] = mapped_column(Integer, nullable=False)
    transmission_rate: Mapped[float] = mapped_column(Float, nullable=False)
    latency: Mapped[float] = mapped_column(Float, nullable=False)
    protocol_type: Mapped[int] = mapped_column(Integer, nullable=False)
    active_connections: Mapped[int] = mapped_column(Integer, nullable=False)
    cpu_usage: Mapped[float] = mapped_column(Float, nullable=False)
    memory_usage: Mapped[float] = mapped_column(Float, nullable=False)
    bandwidth_utilization: Mapped[float] = mapped_column(Float, nullable=False)
    request_response_time: Mapped[float] = mapped_column(Float, nullable=False)
    auth_failures: Mapped[int] = mapped_column(Integer, nullable=False)
    access_violations: Mapped[int] = mapped_column(Integer, nullable=False)
    firewall_blocks: Mapped[int] = mapped_column(Integer, nullable=False)
    ids_alerts: Mapped[int] = mapped_column(Integer, nullable=False)

    prediction: Mapped["PredictionRecord"] = relationship(back_populates="metric")


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric_id: Mapped[int] = mapped_column(ForeignKey("metrics.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    features_json: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    packet_size: Mapped[int] = mapped_column(Integer, nullable=False)
    transmission_rate: Mapped[float] = mapped_column(Float, nullable=False)
    latency: Mapped[float] = mapped_column(Float, nullable=False)
    protocol_type: Mapped[int] = mapped_column(Integer, nullable=False)
    active_connections: Mapped[int] = mapped_column(Integer, nullable=False)
    cpu_usage: Mapped[float] = mapped_column(Float, nullable=False)
    memory_usage: Mapped[float] = mapped_column(Float, nullable=False)
    bandwidth_utilization: Mapped[float] = mapped_column(Float, nullable=False)
    request_response_time: Mapped[float] = mapped_column(Float, nullable=False)
    auth_failures: Mapped[int] = mapped_column(Integer, nullable=False)
    access_violations: Mapped[int] = mapped_column(Integer, nullable=False)
    firewall_blocks: Mapped[int] = mapped_column(Integer, nullable=False)
    ids_alerts: Mapped[int] = mapped_column(Integer, nullable=False)
    failure_probability: Mapped[float] = mapped_column(Float, nullable=False)
    failure_prediction: Mapped[int] = mapped_column(Integer, nullable=False)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, nullable=False)

    metric: Mapped[MetricRecord] = relationship(back_populates="prediction")


class IncidentRecord(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    root_cause: Mapped[str] = mapped_column(String(255), nullable=False)


def create_tables() -> None:
    _archive_incompatible_sqlite_tables()
    Base.metadata.create_all(bind=engine)


def _archive_incompatible_sqlite_tables() -> None:
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if not {"metrics", "predictions"}.intersection(table_names):
        return

    required_prediction_columns = {"features_json", "packet_size", "cpu_usage", "ids_alerts"}
    if "predictions" in table_names:
        prediction_columns = {column["name"] for column in inspector.get_columns("predictions")}
        if required_prediction_columns.issubset(prediction_columns):
            return

    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    with engine.begin() as connection:
        for table_name in ["predictions", "metrics", "incidents"]:
            if table_name in table_names:
                connection.execute(
                    text(f"ALTER TABLE {table_name} RENAME TO {table_name}_legacy_{suffix}")
                )
