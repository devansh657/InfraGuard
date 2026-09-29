# InfraGuard AI Model Card

## Model Purpose

InfraGuard AI predicts anomalous network/infrastructure load from telemetry and detects unusual behavior patterns for monitoring and security analysis.

## Dataset

- Source: protected telemetry stream packaged for local replay
- Rows: 5,000
- Target: protected elevated-risk label
- Class distribution: 3,646 normal rows and 1,354 anomalous rows

## Input Features

The model uses packet, protocol, host-resource, and security-event signals:

- Packet and network flow: `Packet_Size`, `Transmission_Rate`, `Latency`, `Protocol_Type`, `Active_Connections`
- Host/system pressure: `CPU_Usage`, `Memory_Usage`, `Bandwidth_Utilization`, `Request_Response_Time`
- Security events: `Auth_Failures`, `Access_Violations`, `Firewall_Blocks`, `IDS_Alerts`
- Signal features: `DWT_Feature_1` through `DWT_Feature_8`
- Engineered features: rolling means and burst/spike flags

## Production Models

- Supervised prediction: `RandomForestClassifier`
- Unsupervised anomaly detection: `IsolationForest`
- Scaling: `StandardScaler`
- Reproducibility: `random_state=42`

## Evaluation

Latest holdout metrics for the supervised model:

- Accuracy: `0.9960`
- Precision: `1.0000`
- Recall: `0.9852`
- F1-score: `0.9926`
- ROC AUC: `1.0000`
- Average precision: `0.9999`

Model-comparison artifacts are available in:

- `docs/eda/model_benchmark.md`
- `docs/eda/model_benchmark.json`
- `docs/eda/model_comparison.png`
- `docs/eda/roc_comparison.png`

## Explainability

The API returns a ranked contribution list for each supervised prediction using feature importance weighted by the sample's scaled feature magnitude. The EDA report also includes global Random Forest feature importance.

## Known Limitations

- The near-perfect ROC AUC suggests the dataset is highly separable. Any public or academic explanation should explicitly discuss possible synthetic-data effects, proxy variables, and feature leakage risk.
- The model predicts anomalous load from the protected telemetry schema; it is not yet validated on independently collected production traffic.
- The explanation method is a practical feature-contribution approximation, not a full causal explanation.

## Responsible Use

InfraGuard AI should support security and infrastructure triage. It should not be used as the only decision-maker for blocking users, shutting down systems, or declaring incidents without human review.
