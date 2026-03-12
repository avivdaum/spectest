from __future__ import annotations

import pytest

from rf_automation.evaluator import default_limits_for_case, evaluate_metrics
from rf_automation.models import CaseMetrics, Limits, TestCase


@pytest.mark.unit
def test_default_limits_use_plan_defaults():
    case = TestCase(
        id="c",
        tx_mode="cw",
        center_freq_hz=1.0e9,
        span_hz=4.0e6,
        rbw_hz=1.0e3,
        ref_level_dbm=-30.0,
    )
    limits = default_limits_for_case(case)
    assert limits.freq_error_hz_max == 1.0e6
    assert limits.peak_power_dbm_min == -110.0
    assert limits.peak_power_dbm_max == -20.0
    assert limits.obw_hz_min == 1000.0
    assert limits.obw_hz_max == 4.0e6


@pytest.mark.unit
def test_evaluate_metrics_failures():
    metrics = CaseMetrics(
        peak_power_dbm=-5.0,
        peak_freq_hz=100.0,
        freq_error_hz=10.0,
        occupied_bw_hz=80.0,
    )
    limits = Limits(
        freq_error_hz_max=5.0,
        peak_power_dbm_min=-20.0,
        peak_power_dbm_max=-10.0,
        obw_hz_min=90.0,
        obw_hz_max=200.0,
    )
    passed, reasons = evaluate_metrics(metrics, limits)
    assert not passed
    assert len(reasons) == 3
