"""Small formatting helpers shared by the AR processor and validator."""
import pandas as pd

# Re-export so callers have one import site.
from backend.services.ar_processor import clean_string  # noqa: F401


def normalize_series(series: pd.Series) -> pd.Series:
    """
    Strip and upper-case every string cell. NaN/None become "".
    Non-string scalars (ints, floats) are stringified first.
    """
    return (
        series
        .where(series.notna(), "")
        .astype(str)
        .str.strip()
        .str.upper()
        .replace({"NAN": "", "NONE": ""})
    )