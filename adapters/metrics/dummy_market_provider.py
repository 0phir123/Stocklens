from __future__ import annotations  # lazy annotations

from datetime import date, timedelta  # 'date' for today; 'timedelta' for stepping days
from typing import Optional, List  # Optional for params; List for local type hint
import math  # use sin() to make a non-flat dummy series

from core.metrics.entities import Series, SeriesPoint  # domain types (Series alias + SeriesPoint)
from core.metrics.ports import MarketDataPort  # the Port interface we implement


class DummyMarketDataAdapter(MarketDataPort):  # class conforms to MarketDataPort
    def get_adjusted_close(  # implement the required method (same name/signature)
        self,
        symbol: str,
        start: Optional[date] = None,
        end: Optional[date] = None,
        freq: str = "D",
    ) -> Series:  # declare the domain return type
        today = date.today()  # compute today's date (used for defaults)
        start = start or (today - timedelta(days=9))  # default: 10-day window starting 9 days ago
        end = end or today  # default: ends today if not provided

        if start > end:  # simple guardrail for invalid range
            raise ValueError(
                "start must be <= end"
            )  # raise ValueError (service/route will map to HTTP 400)

        step = 1 if freq.upper() == "D" else 30 if freq.upper() == "M" else 90
        # ^ crude resampling: daily=1-day steps, monthly≈30-day steps, quarterly≈90-day steps

        points: List[SeriesPoint] = []  # local list to accumulate domain points
        days = (end - start).days  # integer number of days in window
        base = 100 + (hash(symbol) % 50)  # deterministic per-symbol base price (varies per symbol)

        for i in range(0, days + 1, step):  # iterate inclusive over the window with chosen step
            value = base + 5 * math.sin(i / 3)  # simple wave to avoid flat line (toy data)
            points.append(  # append a new domain value object to the list
                SeriesPoint(
                    when=start + timedelta(days=i),  # date for this point
                    value=round(value, 2),  # round to 2 decimals like prices
                )
            )

        return points  # return a 'Series' (List[SeriesPoint]) as promised
