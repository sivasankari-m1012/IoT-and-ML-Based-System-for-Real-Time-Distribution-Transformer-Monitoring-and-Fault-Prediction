"""Import the old v1 data.csv into the database (keeps your history).

    python scripts/import_csv.py path/to/data.csv --transformer-id 1
Expected columns: Time, Temperature, Voltage, Current, Oil_Percentage, Status
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Reading  # noqa: E402
from app.services.readings import get_or_create_transformer  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--transformer-id", type=int, default=1)
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    needed = {"Time", "Temperature", "Voltage", "Current", "Oil_Percentage", "Status"}
    if needed - set(df.columns):
        sys.exit(f"CSV is missing columns: {sorted(needed - set(df.columns))}")
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
    df = df.dropna(subset=["Time", "Temperature", "Voltage", "Current", "Oil_Percentage"])

    app = create_app()
    with app.app_context():
        transformer = get_or_create_transformer(args.transformer_id)
        for row in df.itertuples():
            status = str(row.Status).upper()
            db.session.add(Reading(
                transformer_id=transformer.id, timestamp=row.Time.to_pydatetime(),
                temperature=row.Temperature, voltage=row.Voltage, current=row.Current,
                oil_percentage=row.Oil_Percentage, power=round(row.Voltage * row.Current, 3),
                status=status if status in {"NORMAL", "WARNING", "FAULT", "OFF"} else "NORMAL",
                reasons=["Imported from v1 CSV"],
            ))
        db.session.commit()
        print(f"Imported {len(df)} readings into transformer {transformer.id}")


if __name__ == "__main__":
    main()
