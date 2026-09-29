from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from time import perf_counter


@dataclass
class RuntimeMetrics:
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_monotonic: float = field(default_factory=perf_counter)
    request_count: int = 0
    rate_limit_hits: int = 0
    invalid_request_count: int = 0
    prediction_count: int = 0
    prediction_latency_ms_total: float = 0.0
    request_latency_ms_total: float = 0.0
    lock: Lock = field(default_factory=Lock)

    def record_request(self, latency_ms: float) -> None:
        with self.lock:
            self.request_count += 1
            self.request_latency_ms_total += latency_ms

    def record_invalid_request(self) -> None:
        with self.lock:
            self.invalid_request_count += 1

    def record_rate_limit_hit(self) -> None:
        with self.lock:
            self.rate_limit_hits += 1

    def record_prediction(self, latency_ms: float) -> None:
        with self.lock:
            self.prediction_count += 1
            self.prediction_latency_ms_total += latency_ms

    def snapshot(self) -> dict[str, float | int | str]:
        with self.lock:
            uptime_seconds = perf_counter() - self.started_monotonic
            avg_request_ms = (
                self.request_latency_ms_total / self.request_count
                if self.request_count
                else 0.0
            )
            avg_prediction_ms = (
                self.prediction_latency_ms_total / self.prediction_count
                if self.prediction_count
                else 0.0
            )
            return {
                "started_at": self.started_at.isoformat(),
                "uptime_seconds": round(uptime_seconds, 2),
                "request_count": self.request_count,
                "rate_limit_hits": self.rate_limit_hits,
                "invalid_request_count": self.invalid_request_count,
                "prediction_count": self.prediction_count,
                "avg_request_latency_ms": round(avg_request_ms, 2),
                "avg_prediction_latency_ms": round(avg_prediction_ms, 2),
            }


runtime_metrics = RuntimeMetrics()
