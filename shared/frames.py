from __future__ import annotations
from typing import Sequence
import pandas as pd
from core.metrics.entities import SeriesPoint


def price_points_to_df(points: Sequence[SeriesPoint]) -> pd.DataFrame:
    dates = [p.when for p in points]
    values = [p.value for p in points]
    df = pd.DataFrame({"date": dates, "value": values})
    df.set_index("date", inplace=True)
    return df
