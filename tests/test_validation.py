# File: tests/test_validation.py
from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional
from core.metrics.validation import SeriesPoint
from services.validation_service import ValidationService


def _mk_points(
    n: int = 14,
    days: int = 30,
    start: Optional[datetime] = None,
    base: float = 100.0,
    step: float = 1.0,
) -> List[SeriesPoint]:
    start = start or datetime(2020, 1, 31)
    pts: List[SeriesPoint] = []
    for i in range(n):
        ts = start + timedelta(days=i * days)
        pts.append(SeriesPoint(ts=ts, value=base + i * step))
    return pts


def test_monthly_series_is_clean_and_valid() -> None:
    svc = ValidationService()
    points = _mk_points(n=72, days=30)  # ~72 months
    clean, report = svc.run(points, freq="M", symbol_key="macro.cpi")
    assert report.is_valid
    assert report.metrics.get("total_observations_out") == len(clean)
    assert clean == sorted(clean, key=lambda p: p.ts)
    assert "stale_data" in report.warnings or "days_old" in report.metrics


def test_daily_gaps_trigger_warning_but_not_always_invalid() -> None:
    svc = ValidationService()
    start = datetime(2024, 1, 1)
    pts = [SeriesPoint(start + timedelta(days=i), 100 + i * 0.1) for i in range(30)]
    pts.append(SeriesPoint(start + timedelta(days=50), 103.0))
    clean, report = svc.run(pts, freq="D", symbol_key="SPY")
    assert report.metrics.get("gaps_count", 0) >= 1
    assert report.is_valid or ("catastrophic_gaps" in report.errors)


def test_outliers_count_metric_present_when_configured() -> None:
    svc = ValidationService()
    points = _mk_points(n=24, days=30, base=200.0, step=0.5)
    points[20] = SeriesPoint(points[20].ts, points[20].value * 1.2)
    clean, report = svc.run(points, freq="M", symbol_key="macro.cpi")
    assert "outliers_count" in report.metrics
    assert report.metrics["outliers_count"] >= 0
