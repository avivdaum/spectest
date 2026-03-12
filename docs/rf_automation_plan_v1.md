# USRP + RSA Automation v1 (3 Test Modes)

## Summary

- Create a new Python project in `C:\Users\efrat\Documents\dev` for RF automation.
- Support exactly 3 modes:
1. `no_hardware` (no RSA, no USRP): hybrid input (recorded traces first, synthetic fallback).
2. `rsa_only` (RSA connected, no USRP): analyzer health and pipeline checks.
3. `full_hw` (RSA + USRP connected): full RF smoke validation.
- First implementation action: save this plan to `C:\Users\efrat\Documents\dev\docs\rf_automation_plan_v1.md`.

## Implementation Changes

- Scaffold project:
  - `src/rf_automation/`, `tests/`, `configs/`, `replay_data/`, `reports/`, `docs/`.
- Add JSON-driven case/config system:
  - `configs/cases.json` for test cases and per-case limits.
  - `configs/run_profile.json` for mode selection and runtime options.
- Define core interfaces:
  - `TxAdapter`: `connect/start_case/wait_ready/stop_case/disconnect`.
  - `RsaClient`: `connect/preset/configure_spectrum/acquire_trace/get_status/disconnect`.
- Implement clients:
  - `LiveRsaClient` via `ctypes` + `RSA_API.dll`.
  - `MockRsaClient` for deterministic synthetic traces.
  - `ReplayTraceProvider` for recorded traces used by `no_hardware`.
- Implement orchestrator:
  - Common case runner with settle + retry policy.
  - Mode-specific behavior:
    - `no_hardware`: replay/mocked traces only.
    - `rsa_only`: TX skipped, RSA health + acquisition pipeline checks.
    - `full_hw`: TX adapter + live RSA measurement flow.
- Implement metrics and verdict:
  - `peak_power_dbm`, `peak_freq_hz`, `freq_error_hz`, `occupied_bw_hz`.
  - Per-case limits; broad sanity defaults when missing.
- Implement reporting:
  - `reports/<timestamp>/report.html`, `summary.csv`, per-case `result.json`, `trace.npz`, `trace_plot.png`.
- Add pytest integration:
  - Markers: `unit`, `no_hardware`, `rsa_only`, `full_hw`.
  - CLI examples through pytest markers and config selection.

## Test Plan

- Unit tests:
  - JSON parsing/validation, metric math, limits evaluation, retry logic, artifact generation.
- `no_hardware` tests:
  - Recorded trace pass/fail, synthetic fallback, deterministic outputs.
- `rsa_only` tests:
  - RSA discovery, preset/configure/acquire path, status handling, report generation.
- `full_hw` tests:
  - End-to-end TX + RSA case run, pass/fail decisions, retries, and outputs.

## Assumptions and Defaults

- Windows environment with Tektronix RSA API installed and DLL reachable.
- USRP TX control will be integrated through a Python `TxAdapter`.
- `no_hardware` prefers recorded traces in `replay_data/`; synthetic fallback if file missing.
- Default runtime values (if not provided): `settle_ms=500`, `max_retries=2`.

