from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

VALID_MODES = {"no_hardware", "rsa_only", "full_hw"}


@dataclass(slots=True)
class Limits:
    freq_error_hz_max: float | None = None
    peak_power_dbm_min: float | None = None
    peak_power_dbm_max: float | None = None
    obw_hz_min: float | None = None
    obw_hz_max: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Limits":
        data = data or {}
        return cls(
            freq_error_hz_max=_to_float_or_none(data.get("freq_error_hz_max")),
            peak_power_dbm_min=_to_float_or_none(data.get("peak_power_dbm_min")),
            peak_power_dbm_max=_to_float_or_none(data.get("peak_power_dbm_max")),
            obw_hz_min=_to_float_or_none(data.get("obw_hz_min")),
            obw_hz_max=_to_float_or_none(data.get("obw_hz_max")),
        )

    def with_fallback(self, fallback: "Limits") -> "Limits":
        return Limits(
            freq_error_hz_max=(
                self.freq_error_hz_max
                if self.freq_error_hz_max is not None
                else fallback.freq_error_hz_max
            ),
            peak_power_dbm_min=(
                self.peak_power_dbm_min
                if self.peak_power_dbm_min is not None
                else fallback.peak_power_dbm_min
            ),
            peak_power_dbm_max=(
                self.peak_power_dbm_max
                if self.peak_power_dbm_max is not None
                else fallback.peak_power_dbm_max
            ),
            obw_hz_min=(
                self.obw_hz_min if self.obw_hz_min is not None else fallback.obw_hz_min
            ),
            obw_hz_max=(
                self.obw_hz_max if self.obw_hz_max is not None else fallback.obw_hz_max
            ),
        )

    def to_dict(self) -> dict[str, float | None]:
        return {
            "freq_error_hz_max": self.freq_error_hz_max,
            "peak_power_dbm_min": self.peak_power_dbm_min,
            "peak_power_dbm_max": self.peak_power_dbm_max,
            "obw_hz_min": self.obw_hz_min,
            "obw_hz_max": self.obw_hz_max,
        }


@dataclass(slots=True)
class TestCase:
    __test__ = False

    id: str
    tx_mode: str
    center_freq_hz: float
    span_hz: float
    rbw_hz: float
    ref_level_dbm: float
    settle_ms: int | None = None
    max_retries: int | None = None
    tx_params: dict[str, Any] = field(default_factory=dict)
    limits: Limits = field(default_factory=Limits)
    replay_file: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestCase":
        return cls(
            id=str(data["id"]),
            tx_mode=str(data["tx_mode"]),
            center_freq_hz=float(data["center_freq_hz"]),
            span_hz=float(data["span_hz"]),
            rbw_hz=float(data["rbw_hz"]),
            ref_level_dbm=float(data["ref_level_dbm"]),
            settle_ms=_to_int_or_none(data.get("settle_ms")),
            max_retries=_to_int_or_none(data.get("max_retries")),
            tx_params=dict(data.get("tx_params") or {}),
            limits=Limits.from_dict(data.get("limits")),
            replay_file=str(data["replay_file"]) if data.get("replay_file") else None,
        )


@dataclass(slots=True)
class RunProfile:
    mode: str = "no_hardware"
    settle_ms: int = 500
    max_retries: int = 2
    timeout_ms: int = 1500
    reports_root: Path = Path("reports")
    replay_root: Path = Path("replay_data")
    rsa_dll_path: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunProfile":
        mode = str(data.get("mode", "no_hardware"))
        if mode not in VALID_MODES:
            raise ValueError(
                f"Unsupported mode: {mode}. Expected one of {sorted(VALID_MODES)}"
            )
        return cls(
            mode=mode,
            settle_ms=int(data.get("settle_ms", 500)),
            max_retries=int(data.get("max_retries", 2)),
            timeout_ms=int(data.get("timeout_ms", 1500)),
            reports_root=Path(data.get("reports_root", "reports")),
            replay_root=Path(data.get("replay_root", "replay_data")),
            rsa_dll_path=data.get("rsa_dll_path"),
        )


@dataclass(slots=True)
class Acquisition:
    freq_hz: np.ndarray
    trace_dbm: np.ndarray
    status: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CaseMetrics:
    peak_power_dbm: float
    peak_freq_hz: float
    freq_error_hz: float
    occupied_bw_hz: float

    def to_dict(self) -> dict[str, float]:
        return {
            "peak_power_dbm": self.peak_power_dbm,
            "peak_freq_hz": self.peak_freq_hz,
            "freq_error_hz": self.freq_error_hz,
            "occupied_bw_hz": self.occupied_bw_hz,
        }


@dataclass(slots=True)
class CaseResult:
    case_id: str
    mode: str
    passed: bool
    reasons: list[str]
    retries_used: int
    metrics: CaseMetrics | None
    limits: Limits | None
    acq_status: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    artifacts: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "case_id": self.case_id,
            "mode": self.mode,
            "passed": self.passed,
            "reasons": self.reasons,
            "retries_used": self.retries_used,
            "acq_status": self.acq_status,
            "error": self.error,
            "artifacts": self.artifacts,
        }
        out["metrics"] = self.metrics.to_dict() if self.metrics else None
        out["limits"] = self.limits.to_dict() if self.limits else None
        return out


@dataclass(slots=True)
class RunResult:
    run_id: str
    mode: str
    results: list[CaseResult]
    report_dir: Path

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)


def _to_float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _to_int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
