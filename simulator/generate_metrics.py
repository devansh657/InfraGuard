"""Generate synthetic infrastructure telemetry for InfraGuard AI.

The output CSV is intentionally simple and stable so later ML phases can load it
without extra dependencies.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


DEFAULT_RECORDS = 7200
DEFAULT_SEED = 42
DEFAULT_OUTPUT = Path(__file__).with_name("system_metrics.csv")


@dataclass(frozen=True)
class MetricRecord:
    timestamp: str
    cpu: float
    memory: float
    latency: float
    error_rate: float
    label: int


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def choose_failure_windows(record_count: int, rng: random.Random) -> list[tuple[int, int]]:
    """Create short incident windows that produce realistic failure labels."""
    window_count = max(3, record_count // 1200)
    windows: list[tuple[int, int]] = []
    latest_start = max(1, record_count - 180)

    for _ in range(window_count):
        start = rng.randint(120, latest_start)
        duration = rng.randint(25, 95)
        windows.append((start, min(record_count, start + duration)))

    return sorted(windows)


def active_failure_pressure(index: int, windows: list[tuple[int, int]]) -> float:
    for start, end in windows:
        if start <= index < end:
            progress = (index - start) / max(1, end - start)
            return 0.65 + 0.35 * math.sin(progress * math.pi)
    return 0.0


def generate_metrics(
    record_count: int = DEFAULT_RECORDS,
    seed: int = DEFAULT_SEED,
    start_time: datetime | None = None,
) -> list[MetricRecord]:
    rng = random.Random(seed)
    windows = choose_failure_windows(record_count, rng)
    start = start_time or datetime.now(timezone.utc).replace(microsecond=0)
    records: list[MetricRecord] = []

    cpu = rng.uniform(28, 45)
    memory = rng.uniform(35, 52)
    latency = rng.uniform(80, 140)
    error_rate = rng.uniform(0.05, 0.45)

    for index in range(record_count):
        daily_wave = math.sin(index / 1440 * 2 * math.pi)
        short_wave = math.sin(index / 90 * 2 * math.pi)
        pressure = active_failure_pressure(index, windows)
        warning_pressure = max(0.0, math.sin(index / 550 * math.pi)) * 0.18

        cpu += rng.gauss(0, 2.1) + daily_wave * 0.6 + pressure * rng.uniform(8, 16)
        memory += rng.gauss(0, 1.6) + daily_wave * 0.35 + pressure * rng.uniform(5, 11)
        latency += rng.gauss(0, 8.0) + short_wave * 1.8 + pressure * rng.uniform(35, 80)
        error_rate += rng.gauss(0, 0.08) + pressure * rng.uniform(0.6, 1.8)

        if rng.random() < 0.018:
            cpu += rng.uniform(8, 20)
            latency += rng.uniform(40, 120)
        if rng.random() < 0.012:
            error_rate += rng.uniform(1.0, 4.5)

        cpu = clamp(cpu * 0.92 + (38 + daily_wave * 8 + warning_pressure * 100) * 0.08, 1, 100)
        memory = clamp(memory * 0.95 + (44 + daily_wave * 5 + warning_pressure * 80) * 0.05, 1, 100)
        latency = clamp(latency * 0.9 + (110 + warning_pressure * 400) * 0.1, 10, 2500)
        error_rate = clamp(error_rate * 0.88 + warning_pressure * 2.2, 0, 100)

        is_failure = (
            pressure > 0
            or cpu >= 92
            or memory >= 94
            or latency >= 900
            or error_rate >= 8.0
        )

        records.append(
            MetricRecord(
                timestamp=(start + timedelta(minutes=index)).isoformat(),
                cpu=round(cpu, 2),
                memory=round(memory, 2),
                latency=round(latency, 2),
                error_rate=round(error_rate, 3),
                label=1 if is_failure else 0,
            )
        )

    return records


def write_csv(records: list[MetricRecord], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "cpu", "memory", "latency", "error_rate", "label"])
        for record in records:
            writer.writerow(
                [
                    record.timestamp,
                    record.cpu,
                    record.memory,
                    record.latency,
                    record.error_rate,
                    record.label,
                ]
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic system metrics for InfraGuard AI."
    )
    parser.add_argument(
        "--records",
        type=int,
        default=DEFAULT_RECORDS,
        help=f"Number of telemetry rows to generate. Default: {DEFAULT_RECORDS}.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"CSV output path. Default: {DEFAULT_OUTPUT}.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed for reproducible data. Default: {DEFAULT_SEED}.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.records < 5000:
        raise ValueError("Phase 1 requires at least 5000 records.")

    records = generate_metrics(record_count=args.records, seed=args.seed)
    write_csv(records, args.output)

    failures = sum(record.label for record in records)
    print(f"Generated {len(records)} records at {args.output}")
    print(f"Failure labels: {failures} ({failures / len(records):.2%})")


if __name__ == "__main__":
    main()
