# File: shared/config.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import yaml  # type: ignore
from pydantic_settings import BaseSettings, SettingsConfigDict

# Reuse domain types to avoid duplication
from core.metrics.validation import (
    ValidationPolicy,
)  # dataclass defined in core/metrics/validation.py


class Settings(BaseSettings):
    """
    App-wide settings loaded from environment (.env) with sensible defaults.
    Only simple primitives live here; richer policy is loaded via YAML below.
    """

    app_name: str = "dev"
    log_level: str = "DEBUG"
    redis_url: str = "redis://localhost:6379/0"

    # Config file paths (override via env if needed)
    config_dir: str = "shared"
    validation_yaml: str = "data_validation.yaml"
    optimal_params_yaml: str = "optimal_parameters.yaml"  # optional

    # Data provider settings (placeholders)
    use_dummy_market: bool = False
    fred_api_key: str = ""
    data_start: str = "1990-01-01"
    data_end: str = "2025-12-31"

    # Common knobs some services reference
    cache_ttl_daily: int = 900  # 15m
    cache_ttl_periodic: int = 43200  # 12h
    max_lookback_days: int = 3650  # ~10y

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()


def load_validation_policy() -> ValidationPolicy:
    """
    Build a ValidationPolicy by merging:
      - config/optimal_parameters.yaml  (defaults; optional)
      - config/data_validation.yaml     (operational policy; REQUIRED; overrides)
    Returns a typed ValidationPolicy ready for DI.
    """
    cfg_dir = Path(settings.config_dir)

    # ---- 1) Load defaults from optimal_parameters.yaml (safe if missing)
    opt: Dict[str, Any] = {}
    opt_path = cfg_dir / settings.optimal_params_yaml
    if opt_path.exists():
        with opt_path.open("r") as f:
            opt = yaml.safe_load(f) or {}
    dq = opt.get("data_quality", {})  # e.g., min_history_months
    mon = opt.get("monitoring", {})  # e.g., missing_data_alert_threshold

    # ---- 2) Load required data_validation.yaml (raise if missing)
    val_path = cfg_dir / settings.validation_yaml
    if not val_path.exists():
        raise FileNotFoundError(
            f"Validation YAML not found at {val_path}. "
            f"Create {settings.config_dir}/{settings.validation_yaml} first."
        )
    with val_path.open("r") as f:
        val = yaml.safe_load(f) or {}

    # Extract sections with safe fallbacks
    req = val.get("requirements", {}) or {}
    gaps = val.get("gaps", {}) or {}
    fresh = val.get("freshness_days_by_key", {}) or {}
    bounds_by_key = val.get("bounds_by_key", {}) or {}
    change_bounds = val.get("change_bounds", {}) or {}
    zthr = val.get("zscore_thresholds", {}) or {}
    cleaning = val.get("cleaning", {}) or {}
    severity = val.get("severity", {}) or {}
    metrics_block = val.get("metrics", {}) or {}

    # ---- 3) Assemble the policy (YAML → typed dataclass), with validation.yaml taking precedence
    policy = ValidationPolicy(
        validator_version=str(val.get("validator_version", "v1")),
        # History requirements
        min_history_months=int(
            req.get("min_history", {}).get(
                "monthly_months",
                int(dq.get("min_history_months", 60)),
            )
        ),
        min_history_days_daily=int(req.get("min_history", {}).get("daily_days", 252)),
        # Gaps & missing tolerance
        max_gap_days_daily=int(gaps.get("max_gap_days_daily", 5)),
        max_long_gaps_allowed=int(gaps.get("max_long_gaps_allowed", 3)),
        missing_data_alert_threshold=float(
            req.get(
                "missing_data_alert_threshold",
                float(mon.get("missing_data_alert_threshold", 0.05)),
            )
        ),
        # Freshness
        freshness_days_by_key={k: int(v) for k, v in fresh.items() if k != "defaults"},
        freshness_defaults={
            "daily": int((fresh.get("defaults") or {}).get("daily", 2)),
            "monthly": int((fresh.get("defaults") or {}).get("monthly", 60)),
            "quarterly": int((fresh.get("defaults") or {}).get("quarterly", 120)),
        },
        # Bounds
        bounds_by_key={str(k): (float(v[0]), float(v[1])) for k, v in bounds_by_key.items()},
        change_bounds_yoy={
            str(k): (float(v[0]), float(v[1])) for k, v in (change_bounds.get("yoy") or {}).items()
        },
        change_bounds_delta={
            str(k): (float(v[0]), float(v[1]))
            for k, v in (change_bounds.get("delta") or {}).items()
        },
        # Outlier thresholds
        zscore_thresholds={str(k): float(v) for k, v in zthr.items()},
        # Cleaning behavior
        cleaning_drop_nan_inf=bool(cleaning.get("drop_nan_inf", True)),
        cleaning_keep_last_on_duplicate_ts=bool(cleaning.get("keep_last_on_duplicate_ts", True)),
        cleaning_sort_ascending=bool(cleaning.get("sort_ascending", True)),
        # Severity & metrics
        severity_invalid_if=list(severity.get("invalid_if", [])),
        severity_warn_if=list(severity.get("warn_if", [])),
        metrics_include=list(metrics_block.get("include") or []),
    )
    return policy
