# Macro Metrics Keys (Finance Demo)
- **macro.gdp** → FRED `GDPC1` (real GDP, quarterly native). If monthly is requested, derive by **linear interpolation** from quarterly and align to **month-end**.
- **macro.cpi** → FRED `CPIAUCSL` (monthly native, align to month-end).
- **macro.baa** → FRED `BAA` (daily → **monthly mean**, align to month-end). Alias: `macro.baa_yield`.

Resampling rules (adapter):
- Request **D** → pad/ffill to calendar days.
- Request **M** → month-end value (`.last()`).
- Request **Q** → quarter-end value, timestamped to month-end of the quarter.