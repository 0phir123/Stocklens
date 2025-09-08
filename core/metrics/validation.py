# File: core/metrics/validation.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

# near the top: add Optional to imports
from typing import List, Dict, Any, Tuple, Literal, Iterable, Optional
import math
from statistics import mean, pstdev

Freq = Literal["D", "M", "Q"]


@dataclass(frozen=True)
class SeriesPoint:
    ts: datetime
    value: float


@dataclass
class ValidationPolicy:
    validator_version: str
    min_history_months: int
    min_history_days_daily: int
    max_gap_days_daily: int
    max_long_gaps_allowed: int
    missing_data_alert_threshold: float
    freshness_days_by_key: Dict[str, int]
    freshness_defaults: Dict[str, int]
    bounds_by_key: Dict[str, Tuple[float, float]]
    change_bounds_yoy: Dict[str, Tuple[float, float]]
    change_bounds_delta: Dict[str, Tuple[float, float]]
    zscore_thresholds: Dict[str, float]
    cleaning_drop_nan_inf: bool
    cleaning_keep_last_on_duplicate_ts: bool
    cleaning_sort_ascending: bool
    severity_invalid_if: List[str]
    severity_warn_if: List[str]
    metrics_include: List[str]


@dataclass
class DataQualityReport:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metrics: Dict[str, Any]
    version: str


# --- helpers ---
def _zscore_outliers(values: Iterable[float], threshold: float) -> Tuple[int, int]:
    xs = [x for x in values if x is not None and not math.isinf(x) and not math.isnan(x)]
    if len(xs) < 10:
        return (0, len(xs))
    m = mean(xs)
    s = pstdev(xs)
    if s == 0:
        return (0, len(xs))
    out = sum(1 for x in xs if abs((x - m) / s) > threshold)
    return (out, len(xs))


def _is_finite(x: float) -> bool:
    return x is not None and not math.isnan(x) and not math.isinf(x)


# --- main entrypoint ---
def validate_series(
    points: List[SeriesPoint], freq: Freq, symbol_key: str, policy: ValidationPolicy
) -> Tuple[List[SeriesPoint], DataQualityReport]:
    errors: List[str] = []
    warnings: List[str] = []
    metrics: Dict[str, Any] = {}

    # Keep a copy for counts
    points_in = list(points)

    # 1) Sort
    pts = (
        sorted(points_in, key=lambda p: p.ts) if policy.cleaning_sort_ascending else list(points_in)
    )

    # 2) Dedup on ts (keep last)
    dedup: Dict[datetime, float] = {}
    for p in pts:
        dedup[p.ts] = p.value
    pts = [SeriesPoint(ts=t, value=v) for t, v in dedup.items()]
    pts.sort(key=lambda p: p.ts)

    # 3) Drop NaN/Inf
    removed_nan_inf = 0
    clean: List[SeriesPoint] = []
    for p in pts:
        if policy.cleaning_drop_nan_inf and not _is_finite(p.value):
            removed_nan_inf += 1
            continue
        clean.append(p)

    # 4) Early invalid checks
    if not clean:
        errors.append("empty_after_clean")
        report = DataQualityReport(False, errors, warnings, {}, policy.validator_version)
        return ([], report)

    # 5) Gaps (simple count)
    gaps_count = 0
    long_gaps = 0
    if freq == "D":
        for i in range(1, len(clean)):
            delta_days = (clean[i].ts - clean[i - 1].ts).days
            if delta_days > policy.max_gap_days_daily:
                gaps_count += 1
                if delta_days > (policy.max_gap_days_daily * 3):
                    long_gaps += 1
    # For M/Q we trust adapter’s alignment; verify monotonic increase only
    # (Optionally: detect missing months/quarters by calendar math)

    # 6) Freshness
    now = datetime.utcnow()
    latest_ts = clean[-1].ts
    days_old = (now - latest_ts).days
    # per-key override → else defaults by freq
    fresh_limit = policy.freshness_days_by_key.get(symbol_key)
    if fresh_limit is None:
        fresh_limit = policy.freshness_defaults[
            "daily" if freq == "D" else ("quarterly" if freq == "Q" else "monthly")
        ]
    if days_old > fresh_limit:
        warnings.append("stale_data")

    # 7) History sufficiency
    if freq in ("M", "Q"):
        if len(clean) < policy.min_history_months:
            errors.append("insufficient_history")
    elif freq == "D":
        if len(clean) < policy.min_history_days_daily:
            errors.append("insufficient_history")

    # 8) Catastrophic gaps rule
    if long_gaps > policy.max_long_gaps_allowed:
        errors.append("catastrophic_gaps")

    # 9) Outliers (optional counts only)
    outliers_count = 0

    # CPI YoY outliers (M/Q)
    if freq in ("M", "Q") and len(clean) >= 13 and symbol_key == "macro.cpi":
        vals = [p.value for p in clean]
        yoy: List[Optional[float]] = []
        for i in range(12, len(vals)):
            prev = vals[i - 12]
            cur = vals[i]
            if prev is None or prev == 0:
                yoy.append(None)
            else:
                yoy.append((cur / prev - 1.0) * 100.0)
        thr = policy.zscore_thresholds.get("inflation_yoy")
        if thr is not None:
            # filter to finite floats before running z-score
            yoy_floats: List[float] = [v for v in yoy if v is not None and _is_finite(v)]
            oc, _ = _zscore_outliers(yoy_floats, thr) if yoy_floats else (0, 0)
            outliers_count += oc

    # BAA delta outliers (first difference)
    if symbol_key == "macro.baa" and len(clean) >= 3:
        vals = [p.value for p in clean]
        deltas: List[Optional[float]] = [None]  # first diff is None
        for i in range(1, len(vals)):
            deltas.append(vals[i] - vals[i - 1] if vals[i - 1] is not None else None)
        thr = policy.zscore_thresholds.get("baa_delta")
        if thr is not None:
            delta_floats: List[float] = [d for d in deltas if d is not None and _is_finite(d)]
            oc, _ = _zscore_outliers(delta_floats, thr) if delta_floats else (0, 0)
            outliers_count += oc
    # 10) Metrics (controlled by YAML)
    inc = set(policy.metrics_include)
    if "total_observations_in" in inc:
        metrics["total_observations_in"] = len(points_in)
    if "total_observations_out" in inc:
        metrics["total_observations_out"] = len(clean)
    if "removed_nan_inf" in inc:
        metrics["removed_nan_inf"] = removed_nan_inf
    if "gaps_count" in inc:
        metrics["gaps_count"] = gaps_count
    if "latest_ts" in inc:
        metrics["latest_ts"] = latest_ts.isoformat()
    if "days_old" in inc:
        metrics["days_old"] = days_old
    if "outliers_count" in inc:
        metrics["outliers_count"] = outliers_count

    is_valid = len(errors) == 0
    report = DataQualityReport(is_valid, errors, warnings, metrics, policy.validator_version)
    return (clean, report)
