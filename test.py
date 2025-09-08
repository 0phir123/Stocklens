from datetime import datetime, timedelta
from core.metrics.validation import SeriesPoint
from services.validation_service import ValidationService

# Fake monthly CPI-like series
start = datetime(2020, 1, 31)
points = [SeriesPoint(start + timedelta(days=30 * i), 250 + i * 0.5) for i in range(72)]

svc = ValidationService()  # loads YAML → policy
clean, report = svc.run(points, freq="M", symbol_key="macro.cpi")

print(report.is_valid, report.errors, report.warnings)
print(report.metrics)  # will include the 7 keys we configured in YAML
