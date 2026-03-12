from __future__ import annotations

import numpy as np

from .models import Acquisition, CaseMetrics, TestCase


def compute_metrics(acq: Acquisition, case: TestCase) -> CaseMetrics:
    if acq.trace_dbm.size == 0 or acq.freq_hz.size == 0:
        raise ValueError("Acquisition is empty")
    peak_idx = int(np.argmax(acq.trace_dbm))
    peak_power_dbm = float(acq.trace_dbm[peak_idx])
    peak_freq_hz = float(acq.freq_hz[peak_idx])
    freq_error_hz = abs(peak_freq_hz - case.center_freq_hz)
    occupied_bw_hz = occupied_bandwidth_hz(acq.freq_hz, acq.trace_dbm, power_ratio=0.99)
    return CaseMetrics(
        peak_power_dbm=peak_power_dbm,
        peak_freq_hz=peak_freq_hz,
        freq_error_hz=freq_error_hz,
        occupied_bw_hz=occupied_bw_hz,
    )


def occupied_bandwidth_hz(
    freq_hz: np.ndarray,
    trace_dbm: np.ndarray,
    power_ratio: float = 0.99,
) -> float:
    if freq_hz.size < 2 or trace_dbm.size < 2:
        return 0.0
    if not (0.0 < power_ratio <= 1.0):
        raise ValueError("power_ratio must be in (0.0, 1.0]")
    linear_mw = np.power(10.0, trace_dbm / 10.0)
    total = float(np.sum(linear_mw))
    if total <= 0:
        return 0.0
    cdf = np.cumsum(linear_mw) / total
    outer = (1.0 - power_ratio) / 2.0
    low_idx = int(np.searchsorted(cdf, outer, side="left"))
    high_idx = int(np.searchsorted(cdf, 1.0 - outer, side="left"))
    low_idx = max(0, min(low_idx, len(freq_hz) - 1))
    high_idx = max(low_idx, min(high_idx, len(freq_hz) - 1))
    return float(freq_hz[high_idx] - freq_hz[low_idx])

