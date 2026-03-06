from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"


def _metrics(y_true, y_pred, y_prob) -> dict[str, float]:
    return {
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }


def train_and_score() -> pd.DataFrame:
    data = pd.read_csv(PROCESSED_DIR / "features.csv")

    features = [
        "recency_days",
        "frequency",
        "monetary_avg",
        "ticket_volume",
        "resolution_time_avg",
        "social_mentions_count",
        "sentiment_mean",
        "sentiment_trend",
        "clv",
    ]

    x = data[features]
    y = data["churned"]

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.20, random_state=42, stratify=y
    )

    models = {
        "logistic_regression": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=1200, random_state=42)),
            ]
        ),
        "random_forest": RandomForestClassifier(n_estimators=250, random_state=42),
    }

    try:
        from xgboost import XGBClassifier

        models["xgboost"] = XGBClassifier(
            n_estimators=250,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
            eval_metric="logloss",
        )
    except Exception:
        pass

    all_metrics: list[dict] = []
    fitted_models: dict[str, object] = {}

    for name, model in models.items():
        model.fit(x_train, y_train)
        y_prob = model.predict_proba(x_test)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)
        row = {"model": name} | _metrics(y_test, y_pred, y_prob)
        all_metrics.append(row)
        fitted_models[name] = model

    metrics_df = pd.DataFrame(all_metrics).sort_values("roc_auc", ascending=False)
    best_name = str(metrics_df.iloc[0]["model"])
    best_model = fitted_models[best_name]

    full_prob = best_model.predict_proba(x)[:, 1]
    predictions = data[["customer_id", "churned"]].copy()
    predictions["churn_probability"] = full_prob

    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
    elif hasattr(best_model, "named_steps") and hasattr(best_model.named_steps["model"], "coef_"):
        importances = abs(best_model.named_steps["model"].coef_[0])
    else:
        importances = [0.0] * len(features)

    fi = pd.DataFrame({"feature": features, "importance": importances}).sort_values(
        "importance", ascending=False
    )

    metrics_df.to_csv(PROCESSED_DIR / "model_metrics.csv", index=False)
    predictions.to_csv(PROCESSED_DIR / "model_predictions.csv", index=False)
    fi.to_csv(PROCESSED_DIR / "feature_importance.csv", index=False)

    print(f"Best model: {best_name}")
    print(metrics_df.to_string(index=False))
    return metrics_df


if __name__ == "__main__":
    train_and_score()
