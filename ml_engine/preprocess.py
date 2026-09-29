"""Data cleaning, validation, scaling, and splitting helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

try:
    from .utils import (
        BASE_NUMERIC_FEATURES,
        FEATURE_COLUMNS,
        RANDOM_STATE,
        SCALED_FEATURE_COLUMNS,
        TARGET_COLUMN,
    )
except ImportError:
    from utils import (
        BASE_NUMERIC_FEATURES,
        FEATURE_COLUMNS,
        RANDOM_STATE,
        SCALED_FEATURE_COLUMNS,
        TARGET_COLUMN,
    )


@dataclass(frozen=True)
class DatasetSplit:
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    train_frame: pd.DataFrame
    test_frame: pd.DataFrame
    scaler: StandardScaler


def clean_dataset(data: pd.DataFrame) -> pd.DataFrame:
    cleaned = data.copy()
    if "record_index" not in cleaned.columns:
        cleaned.insert(0, "record_index", range(len(cleaned)))

    for column in BASE_NUMERIC_FEATURES + [TARGET_COLUMN]:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned = cleaned.replace([np.inf, -np.inf], np.nan)
    cleaned = cleaned.dropna(subset=[*BASE_NUMERIC_FEATURES, TARGET_COLUMN])

    valid_bounds = cleaned[TARGET_COLUMN].isin([0, 1])
    cleaned = cleaned.loc[valid_bounds].copy()
    cleaned[TARGET_COLUMN] = cleaned[TARGET_COLUMN].astype(int)
    cleaned["record_index"] = pd.to_numeric(cleaned["record_index"], errors="coerce")
    cleaned = cleaned.dropna(subset=["record_index"])
    cleaned["record_index"] = cleaned["record_index"].astype(int)

    return cleaned.sort_values("record_index").reset_index(drop=True)


def fit_scaler(data: pd.DataFrame) -> StandardScaler:
    scaler = StandardScaler()
    scaler.fit(data[SCALED_FEATURE_COLUMNS])
    return scaler


def apply_scaler(data: pd.DataFrame, scaler: StandardScaler) -> pd.DataFrame:
    scaled = data.copy()
    scaled[SCALED_FEATURE_COLUMNS] = scaler.transform(scaled[SCALED_FEATURE_COLUMNS])
    return scaled


def split_records(
    data: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1.")

    train_frame, test_frame = train_test_split(
        data,
        test_size=test_size,
        random_state=random_state,
        stratify=data[TARGET_COLUMN],
    )

    return (
        train_frame.sort_values("record_index").reset_index(drop=True),
        test_frame.sort_values("record_index").reset_index(drop=True),
    )


def scale_feature_splits(
    train_frame: pd.DataFrame,
    test_frame: pd.DataFrame,
) -> DatasetSplit:
    scaler = fit_scaler(train_frame)
    train_scaled = apply_scaler(train_frame, scaler)
    test_scaled = apply_scaler(test_frame, scaler)

    return DatasetSplit(
        X_train=train_scaled[FEATURE_COLUMNS],
        X_test=test_scaled[FEATURE_COLUMNS],
        y_train=train_scaled[TARGET_COLUMN],
        y_test=test_scaled[TARGET_COLUMN],
        train_frame=train_scaled,
        test_frame=test_scaled,
        scaler=scaler,
    )


def split_and_scale(
    data: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = RANDOM_STATE,
) -> DatasetSplit:
    train_frame, test_frame = split_records(data, test_size=test_size, random_state=random_state)
    return scale_feature_splits(train_frame, test_frame)


if __name__ == "__main__":
    try:
        from .dataset_loader import load_dataset
        from .feature_engineering import add_time_series_features
    except ImportError:
        from dataset_loader import load_dataset
        from feature_engineering import add_time_series_features

    frame = add_time_series_features(clean_dataset(load_dataset()))
    split = split_and_scale(frame)
    print(f"Train rows: {len(split.X_train)}")
    print(f"Test rows: {len(split.X_test)}")
