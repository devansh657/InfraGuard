"""Dataset loading utilities for InfraGuard AI telemetry."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from .utils import BASE_NUMERIC_FEATURES, DEFAULT_DATASET_PATH, TARGET_COLUMN, resolve_project_path
except ImportError:
    from utils import BASE_NUMERIC_FEATURES, DEFAULT_DATASET_PATH, TARGET_COLUMN, resolve_project_path


REQUIRED_COLUMNS = [*BASE_NUMERIC_FEATURES, TARGET_COLUMN]


def load_dataset(dataset_path: str | Path = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    path = resolve_project_path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    data = pd.read_csv(path)
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(data.columns))
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    data = data[REQUIRED_COLUMNS].copy()
    data.insert(0, "record_index", range(len(data)))
    return data


if __name__ == "__main__":
    frame = load_dataset()
    print(f"Loaded {len(frame)} rows from {DEFAULT_DATASET_PATH}")
    print(frame.head())
