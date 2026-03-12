from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from ..interfaces import RsaClient, RsaClientError
from ..models import Acquisition, TestCase
from .replay import ReplayTraceProvider


@dataclass
class MockRsaClient(RsaClient):
    replay_provider: ReplayTraceProvider | None = None
    _connected: bool = False
    _current_case: TestCase | None = None
    _status: dict[str, Any] = None

    def __post_init__(self) -> None:
        if self._status is None:
            self._status = {}

    def connect(self) -> None:
        self._connected = True
        self._status = {"connected": True, "source": "mock"}

    def preset(self) -> None:
        if not self._connected:
            raise RsaClientError("MockRsaClient must be connected before preset")

    def configure_spectrum(self, case: TestCase) -> None:
        self._current_case = case
        self._status = {
            "connected": self._connected,
            "source": "mock",
            "configured": True,
        }

    def acquire_trace(self, timeout_ms: int) -> Acquisition:
        del timeout_ms
        if self._current_case is None:
            raise RsaClientError("No case configured on MockRsaClient")
        if self.replay_provider:
            replay = self.replay_provider.load(self._current_case)
            if replay is not None:
                replay.status.setdefault("stable", True)
                self._status = dict(replay.status)
                self._status["connected"] = self._connected
                return replay
        acq = self._generate_synthetic(self._current_case)
        self._status = dict(acq.status)
        self._status["connected"] = self._connected
        return acq

    def get_status(self) -> dict[str, Any]:
        return dict(self._status)

    def disconnect(self) -> None:
        self._connected = False
        self._status = {"connected": False, "source": "mock"}

    def _generate_synthetic(self, case: TestCase) -> Acquisition:
        points = 1024
        start = case.center_freq_hz - case.span_hz / 2.0
        stop = case.center_freq_hz + case.span_hz / 2.0
        freq = np.linspace(start, stop, points, dtype=float)
        seed = abs(hash(case.id)) % (2**32)
        rng = np.random.default_rng(seed)
        noise = rng.normal(loc=-95.0, scale=1.5, size=points)
        sigma = max(case.span_hz * 0.04, 1.0)
        peak = np.exp(-((freq - case.center_freq_hz) ** 2) / (2.0 * sigma**2))
        peak_level = case.ref_level_dbm - 12.0
        trace = noise + peak * (peak_level - noise)
        status = {"source": "synthetic", "stable": True, "seed": int(seed)}
        return Acquisition(freq_hz=freq, trace_dbm=trace, status=status)
