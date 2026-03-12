from __future__ import annotations

from .models import CaseMetrics, Limits, TestCase


def default_limits_for_case(case: TestCase) -> Limits:
    return Limits(
        freq_error_hz_max=case.span_hz / 4.0,
        peak_power_dbm_min=case.ref_level_dbm - 80.0,
        peak_power_dbm_max=case.ref_level_dbm + 10.0,
        obw_hz_min=case.rbw_hz,
        obw_hz_max=case.span_hz,
    )


def effective_limits(case: TestCase) -> Limits:
    return case.limits.with_fallback(default_limits_for_case(case))


def evaluate_metrics(metrics: CaseMetrics, limits: Limits) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if (
        limits.freq_error_hz_max is not None
        and metrics.freq_error_hz > limits.freq_error_hz_max
    ):
        reasons.append(
            f"freq_error_hz {metrics.freq_error_hz:.3f} > {limits.freq_error_hz_max:.3f}"
        )
    if (
        limits.peak_power_dbm_min is not None
        and metrics.peak_power_dbm < limits.peak_power_dbm_min
    ):
        reasons.append(
            f"peak_power_dbm {metrics.peak_power_dbm:.3f} < {limits.peak_power_dbm_min:.3f}"
        )
    if (
        limits.peak_power_dbm_max is not None
        and metrics.peak_power_dbm > limits.peak_power_dbm_max
    ):
        reasons.append(
            f"peak_power_dbm {metrics.peak_power_dbm:.3f} > {limits.peak_power_dbm_max:.3f}"
        )
    if limits.obw_hz_min is not None and metrics.occupied_bw_hz < limits.obw_hz_min:
        reasons.append(
            f"occupied_bw_hz {metrics.occupied_bw_hz:.3f} < {limits.obw_hz_min:.3f}"
        )
    if limits.obw_hz_max is not None and metrics.occupied_bw_hz > limits.obw_hz_max:
        reasons.append(
            f"occupied_bw_hz {metrics.occupied_bw_hz:.3f} > {limits.obw_hz_max:.3f}"
        )
    return len(reasons) == 0, reasons
