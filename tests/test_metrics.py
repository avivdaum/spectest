from __future__ import annotations

import numpy as np
import pytest

from rf_automation.metrics import compute_metrics, occupied_bandwidth_hz
from rf_automation.models import Acquisition, Limits, TestCase


@pytest.mark.unit
def test_occupied_bandwidth_is_positive():
    freq = np.linspace(100.0, 200.0, 1000)
    trace = -100.0 + 40.0 * np.exp(-((freq - 150.0) ** 2) / 200.0)
    obw = occupied_bandwidth_hz(freq, trace)
    assert obw > 0
    assert obw <= (freq[-1] - freq[0])


@pytest.mark.unit
def test_compute_metrics_peak_and_error():
    freq = np.linspace(1000.0, 1100.0, 256)
    trace = np.full(256, -80.0)
    trace[100] = -10.0
    case = TestCase(
        id="metric_case",
        tx_mode="cw",
        center_freq_hz=freq[100],
        span_hz=100.0,
        rbw_hz=1.0,
        ref_level_dbm=-20.0,
        limits=Limits(),
    )
    acq = Acquisition(freq_hz=freq, trace_dbm=trace, status={})
    metrics = compute_metrics(acq, case)
    assert metrics.peak_power_dbm == -10.0
    assert metrics.freq_error_hz == 0.0
