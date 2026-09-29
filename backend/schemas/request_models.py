from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MetricsRequest(BaseModel):
    """Strict request schema for the protected telemetry model."""

    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)

    packet_size: int = Field(..., alias="Packet_Size", ge=0)
    transmission_rate: float = Field(..., alias="Transmission_Rate", ge=0)
    latency: float = Field(..., alias="Latency", ge=0)
    protocol_type: int = Field(..., alias="Protocol_Type", ge=0, le=1)
    active_connections: int = Field(..., alias="Active_Connections", ge=0)
    cpu_usage: float = Field(..., alias="CPU_Usage", ge=0, le=100)
    memory_usage: float = Field(..., alias="Memory_Usage", ge=0)
    bandwidth_utilization: float = Field(..., alias="Bandwidth_Utilization", ge=0, le=100)
    request_response_time: float = Field(..., alias="Request_Response_Time", ge=0)
    auth_failures: int = Field(..., alias="Auth_Failures", ge=0)
    access_violations: int = Field(..., alias="Access_Violations", ge=0)
    firewall_blocks: int = Field(..., alias="Firewall_Blocks", ge=0)
    ids_alerts: int = Field(..., alias="IDS_Alerts", ge=0)
    dwt_feature_1: float = Field(..., alias="DWT_Feature_1")
    dwt_feature_2: float = Field(..., alias="DWT_Feature_2")
    dwt_feature_3: float = Field(..., alias="DWT_Feature_3")
    dwt_feature_4: float = Field(..., alias="DWT_Feature_4")
    dwt_feature_5: float = Field(..., alias="DWT_Feature_5")
    dwt_feature_6: float = Field(..., alias="DWT_Feature_6")
    dwt_feature_7: float = Field(..., alias="DWT_Feature_7")
    dwt_feature_8: float = Field(..., alias="DWT_Feature_8")

    def to_feature_dict(self) -> dict[str, float]:
        return {
            key: float(value)
            for key, value in self.model_dump(by_alias=True).items()
        }

    def primary_metrics(self) -> dict[str, float | int]:
        return {
            "packet_size": self.packet_size,
            "transmission_rate": self.transmission_rate,
            "latency": self.latency,
            "protocol_type": self.protocol_type,
            "active_connections": self.active_connections,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "bandwidth_utilization": self.bandwidth_utilization,
            "request_response_time": self.request_response_time,
            "auth_failures": self.auth_failures,
            "access_violations": self.access_violations,
            "firewall_blocks": self.firewall_blocks,
            "ids_alerts": self.ids_alerts,
        }


class WhatIfRequest(BaseModel):
    """Compare a current telemetry sample against a proposed safer/worse state."""

    model_config = ConfigDict(extra="forbid", strict=True)

    baseline: MetricsRequest
    candidate: MetricsRequest
