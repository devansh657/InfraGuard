from pydantic import BaseModel, ConfigDict, Field


class ExplanationFeature(BaseModel):
    feature: str
    contribution: float


class FailurePredictionResponse(BaseModel):
    failure_probability: float
    prediction: int
    explanation: list[ExplanationFeature] = Field(default_factory=list)


class AnomalyResponse(BaseModel):
    is_anomaly: bool
    score: float


class AnalysisResponse(BaseModel):
    failure: FailurePredictionResponse
    anomaly: AnomalyResponse


class RootCauseResponse(BaseModel):
    feature: str
    category: str
    contribution: float
    severity: str
    evidence: str


class DriftResponse(BaseModel):
    drift_score: float
    level: str
    shifted_features: list[str] = Field(default_factory=list)
    summary: str


class AnalystResponse(BaseModel):
    analysis: AnalysisResponse
    severity: str
    priority_score: int
    confidence: float
    root_causes: list[RootCauseResponse] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    playbook: list[str] = Field(default_factory=list)
    incident_summary: str
    drift: DriftResponse


class WhatIfResponse(BaseModel):
    baseline: AnalystResponse
    candidate: AnalystResponse
    risk_delta: float
    priority_delta: int
    severity_change: str
    impact_summary: str


class NovaPanelResponse(BaseModel):
    label: str
    value: str
    status: str


class NovaBriefingResponse(BaseModel):
    assistant: str
    operational_state: str
    risk_level: str
    spoken_briefing: str
    urgent_alerts: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    system_panels: list[NovaPanelResponse] = Field(default_factory=list)
    command_suggestions: list[str] = Field(default_factory=list)


class LiveTickResponse(BaseModel):
    prediction_id: int
    source: str
    replay_mode: str
    record_index: int
    actual_label: int | None
    features: dict[str, float | int]
    analysis: dict[str, object]
    explanation: str


class LiveStatusResponse(BaseModel):
    source: str
    rows: int
    next_record_index: int
    mode: str


class UploadResponse(BaseModel):
    filename: str
    rows: int
    upload_id: str
    message: str


class PredictionHistoryRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: str
    features: dict[str, float]
    packet_size: int
    transmission_rate: float
    latency: float
    protocol_type: int
    active_connections: int
    cpu_usage: float
    memory_usage: float
    bandwidth_utilization: float
    request_response_time: float
    auth_failures: int
    access_violations: int
    firewall_blocks: int
    ids_alerts: int
    failure_probability: float
    failure_prediction: int
    anomaly_score: float
    is_anomaly: bool


class HistoryResponse(BaseModel):
    records: list[PredictionHistoryRecord]


class ReportResponse(BaseModel):
    total_requests: int
    anomalies: int
    failures: int
    risk_level: str


class HealthResponse(BaseModel):
    status: str
    service: str
    uptime_seconds: float
    ml_models_loaded: bool
    db_connected: bool
    metrics: dict[str, float | int | str]


class FeatureSchemaItem(BaseModel):
    name: str
    description: str
    min: float
    max: float
    mean: float
    median: float
    dtype: str


class ModelInfoResponse(BaseModel):
    target_column: str
    base_feature_columns: list[str]
    feature_columns: list[str]
    feature_defaults: dict[str, float | int]
    feature_schema: list[FeatureSchemaItem]
    feature_config: dict[str, float | int | str]
    failure_metrics: dict[str, float | int | str | list[list[int]]]


class EDAResponse(BaseModel):
    available: bool
    summary: dict[str, object] = {}
    evaluation: dict[str, object] = {}


class BenchmarkReportResponse(BaseModel):
    available: bool
    benchmark: dict[str, object] = {}
