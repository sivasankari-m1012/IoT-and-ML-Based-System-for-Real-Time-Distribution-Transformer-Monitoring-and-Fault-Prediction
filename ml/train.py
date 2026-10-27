"""Train the anomaly model.

    python -m ml.train                       # uses the bundled sample data
    python -m ml.train --data a.xlsx b.csv   # your own labelled data (Status = NORMAL/FAULT)

Approach: Isolation Forest is *novelty detection* - fit on NORMAL rows only, then anything that
looks different from healthy behaviour scores < 0. Labelled FAULT rows are used only to evaluate
(5-fold cross-validation), so the reported numbers are honest, not training-set accuracy.
"""
import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.services.features import FEATURES, build_features  # noqa: E402

DEFAULT_DATA = [ROOT / "ml" / "data" / "training_data.xlsx", ROOT / "ml" / "data" / "sample_readings.csv"]
DEFAULT_OUT = ROOT / "models" / "anomaly_model.joblib"
RAW_COLUMNS = ["Temperature", "Voltage", "Current", "Oil_Percentage", "Status"]


def load_data(paths) -> pd.DataFrame:
    frames = []
    for p in map(Path, paths):
        df = pd.read_excel(p) if p.suffix.lower() in {".xlsx", ".xls"} else pd.read_csv(p)
        missing = set(RAW_COLUMNS) - set(df.columns)
        if missing:
            raise SystemExit(f"{p.name}: missing columns {sorted(missing)}")
        frames.append(df[RAW_COLUMNS])
    df = pd.concat(frames, ignore_index=True)
    df["Status"] = df["Status"].astype(str).str.upper().str.strip()
    df = df[df["Status"].isin(["NORMAL", "FAULT"])].dropna().reset_index(drop=True)  # OFF rows are not sensor behaviour
    return df


def make_pipeline(contamination: float = 0.05) -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            ("forest", IsolationForest(n_estimators=200, contamination=contamination, random_state=42)),
        ]
    )


def fit_model(df: pd.DataFrame) -> Pipeline:
    normal = df[df["Status"] == "NORMAL"]
    return make_pipeline().fit(build_features(normal))


def cross_validate(df: pd.DataFrame, folds: int = 5) -> dict:
    y_true = (df["Status"] == "FAULT").astype(int).to_numpy()
    y_pred = y_true.copy() * 0
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
    for train_idx, test_idx in skf.split(df, y_true):
        train, test = df.iloc[train_idx], df.iloc[test_idx]
        model = fit_model(train)
        y_pred[test_idx] = (model.decision_function(build_features(test)) < 0).astype(int)
    report = classification_report(y_true, y_pred, target_names=["NORMAL", "FAULT"], output_dict=True, zero_division=0)
    return {
        "folds": folds,
        "rows": len(df),
        "fault_precision": round(report["FAULT"]["precision"], 3),
        "fault_recall": round(report["FAULT"]["recall"], 3),
        "fault_f1": round(report["FAULT"]["f1-score"], 3),
        "confusion_matrix [[TN, FP], [FN, TP]]": confusion_matrix(y_true, y_pred).tolist(),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", nargs="+", default=DEFAULT_DATA)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args()

    df = load_data(args.data)
    n_normal, n_fault = (df.Status == "NORMAL").sum(), (df.Status == "FAULT").sum()
    print(f"Loaded {len(df)} labelled rows ({n_normal} NORMAL, {n_fault} FAULT)")

    metrics = cross_validate(df)
    print("Cross-validated metrics:\n" + json.dumps(metrics, indent=2))

    model = fit_model(df)
    meta = {
        "trained_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "features": FEATURES,
        "sklearn_version": sklearn.__version__,
        "training_rows": int((df.Status == "NORMAL").sum()),
        "metrics": metrics,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": model, "meta": meta}, out)
    print(f"Saved model -> {out}")


if __name__ == "__main__":
    main()
