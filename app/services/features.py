"""Single source of truth for model features (used by training AND serving).

The original project trained on [Voltage, Current, Temperature, Power] but served
[Temperature, Voltage, Current, Oil_Percentage] - the mismatch crashed every prediction.
Sharing this module makes that class of bug impossible.
"""
import pandas as pd

FEATURES = ["Temperature", "Voltage", "Current", "Oil_Percentage", "Power"]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Power"] = out["Voltage"] * out["Current"]  # derived: apparent power (VA)
    return out[FEATURES]


def single_row(temperature: float, voltage: float, current: float, oil_percentage: float) -> pd.DataFrame:
    return build_features(
        pd.DataFrame(
            [{"Temperature": temperature, "Voltage": voltage, "Current": current, "Oil_Percentage": oil_percentage}]
        )
    )
