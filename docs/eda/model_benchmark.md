# InfraGuard AI Model Benchmark

Generated: `2026-07-26T16:08:00.616189+00:00`
Target: `protected_risk_label`
Best model by holdout ROC AUC/recall/F1: **Gradient Boosting**

## Holdout Results

| Model | Accuracy | Precision | Recall | F1 | ROC AUC | PR AUC |
|---|---:|---:|---:|---:|---:|---:|
| Gradient Boosting | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Hist Gradient Boosting | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Random Forest | 0.9960 | 1.0000 | 0.9852 | 0.9926 | 1.0000 | 0.9999 |
| Extra Trees | 0.9950 | 0.9963 | 0.9852 | 0.9907 | 0.9962 | 0.9946 |
| Logistic Regression | 0.9660 | 0.8990 | 0.9852 | 0.9401 | 0.9929 | 0.9901 |

## Leakage / Separability Audit

- Max absolute target correlation: `0.7645`
- High-correlation features: `[]`

## Research Notes

- Holdout ROC AUC is near-perfect; the project documentation should discuss dataset separability, synthetic generation risk, and possible feature leakage.
- Use recall and PR AUC alongside ROC AUC because missed anomalies are operationally costly.
