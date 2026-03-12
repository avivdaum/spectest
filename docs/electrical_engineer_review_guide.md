# SpecTest RF Validation Guide (Engineer Review Packet)

## Purpose

This document is for electrical engineers who define RF requirements and review validation results.
It describes:

- What tests are currently covered
- What outputs are generated after each run
- How test cases are configured
- Which open questions must be answered before expanding coverage

---

## Current Test Coverage

### Test Modes

1. `no_hardware`
- No live instruments required
- Uses saved traces (or synthetic traces if no saved trace exists)
- Used for workflow checks and repeatability checks

2. `rsa_only`
- RSA connected, TX source not required
- Used for analyzer health and measurement pipeline readiness checks

3. `full_hw`
- RSA + TX source connected
- Used for end-to-end RF validation against pass/fail limits

### Metrics Covered in RF Validation (`full_hw`)

1. Peak frequency (`peak_freq_hz`)
2. Frequency error from expected center (`freq_error_hz`)
3. Peak power (`peak_power_dbm`)
4. Occupied bandwidth (`occupied_bw_hz`, currently 99% power OBW)

### Pass/Fail Logic

- Each test case can define its own limits.
- If limits are not provided, broad default sanity limits are used.
- Case outcome is `PASS` only if all enabled limits pass.

---

## Results and Artifacts

Each run creates a timestamped folder:

- `reports/<run_id>/report.html`  
Human-readable summary for review

- `reports/<run_id>/summary.csv`  
One row per case with key metrics and verdict

- `reports/<run_id>/cases/<case_id>/result.json`  
Detailed per-case verdict, reasons, and status

- `reports/<run_id>/cases/<case_id>/trace.npz`  
Saved frequency/trace arrays for offline analysis

- `reports/<run_id>/cases/<case_id>/trace_plot.png`  
Spectrum plot image for quick visual inspection

### Recommended Review Flow

1. Open `report.html` for overall status
2. Inspect failed rows in `summary.csv`
3. Open `result.json` and `trace_plot.png` for failed cases
4. Confirm if failure is true RF behavior vs setup/environment issue

---

## Case Configuration (What Engineers Edit)

Case definitions are in:

- `configs/cases.json`

Run-level mode/options are in:

- `configs/run_profile.json`

### Per-Case Fields

Required:

- `id`: unique case name
- `tx_mode`: signal/mode label
- `center_freq_hz`
- `span_hz`
- `rbw_hz`
- `ref_level_dbm`

Optional:

- `settle_ms`
- `max_retries`
- `tx_params` (signal-specific TX settings)
- `limits`

### Limit Fields (Per Case)

- `freq_error_hz_max`
- `peak_power_dbm_min`
- `peak_power_dbm_max`
- `obw_hz_min`
- `obw_hz_max`

### Example Case

```json
{
  "id": "wifi_like_2g4",
  "tx_mode": "ofdm",
  "center_freq_hz": 2445300000.0,
  "span_hz": 40000000.0,
  "rbw_hz": 10000.0,
  "ref_level_dbm": -20.0,
  "settle_ms": 500,
  "max_retries": 2,
  "tx_params": {
    "sample_rate_hz": 20000000.0,
    "gain_db": 45.0
  },
  "limits": {
    "freq_error_hz_max": 10000000.0,
    "peak_power_dbm_min": -80.0,
    "peak_power_dbm_max": 5.0,
    "obw_hz_min": 500000.0,
    "obw_hz_max": 39000000.0
  }
}
```

---

## Questions for Electrical Engineer / Customer Review

Please review and answer the following before next implementation phase.

### A. Signal and Case Definition

1. What exact TX signal families must be covered (CW, OFDM, chirp, burst, etc.)?
2. Which frequencies/bands and channel plans are mandatory?
3. Which operating power levels must be validated per signal?
4. Which test matrix is required (temperature, voltage, cable paths, attenuation states)?

### B. Metric and Limit Requirements

5. Exact allowed frequency error per case (Hz or ppm)?
6. Exact allowed peak power range per case (dBm)?
7. Exact OBW method and thresholds:
- OBW percentage (99% or other)
- Min/max OBW per signal
8. Should limits include guard-band for measurement uncertainty? If yes, how much?

### C. Measurement Method and Analyzer Settings

9. Required RBW/VBW/window/detector settings for each signal type?
10. Single capture vs averaging requirements?
11. Trigger requirements (free-run vs external trigger)?
12. Required reference clock discipline (internal/external)?

### D. Pass/Fail and Reporting Policy

13. Should any failed retry be logged as warning even if final retry passes?
14. Which failures are blocking vs advisory?
15. Required report fields for customer handoff (serials, calibration date, setup photo, etc.)?
16. Required data retention period for raw traces and reports?

### E. Next-Phase Coverage

17. Which additional metrics are required next:
- ACPR
- Harmonics
- Spurious emissions
- Mask compliance
- EVM/modulation quality
18. Which of these are release-gating vs informational?

---

## Suggested Response Template

Use this table format when returning requirements:

| case_id | signal_type | center_freq_hz | power_target_dbm | freq_error_max_hz | peak_power_min_dbm | peak_power_max_dbm | obw_percent | obw_min_hz | obw_max_hz | notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| example_case | OFDM | 2445300000 | -18 | 20000 | -22 | -14 | 99 | 17000000 | 22000000 | include 2 dB uncertainty margin |

