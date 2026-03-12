from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from ..models import Acquisition, TestCase


class ReplayTraceProvider:
    """Loads recorded traces from replay_data for no_hardware mode."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def load(self, case: TestCase) -> Acquisition | None:
        for candidate in self._candidates(case):
            if candidate.suffix.lower() == ".npz" and candidate.exists():
                return self._load_npz(candidate)
            if candidate.suffix.lower() == ".json" and candidate.exists():
                return self._load_json(candidate)
        return None

    def _candidates(self, case: TestCase) -> list[Path]:
        names: list[str] = []
        if case.replay_file:
            names.append(case.replay_file)
        names.append(f"{case.id}.npz")
        names.append(f"{case.id}.json")
        return [self.root / name for name in names]

    def _load_npz(self, path: Path) -> Acquisition:
        payload = np.load(path)
        freq = payload["freq_hz"].astype(float)
        trace = payload["trace_dbm"].astype(float)
        status_raw: Any = (
            payload["status_json"] if "status_json" in payload.files else None
        )
        status: dict[str, Any]
        if status_raw is None:
            status = {}
        else:
            if isinstance(status_raw, np.ndarray):
                status_raw = status_raw.tolist()
            if isinstance(status_raw, bytes):
                status_raw = status_raw.decode("utf-8")
            if isinstance(status_raw, str):
                try:
                    status = json.loads(status_raw)
                except json.JSONDecodeError:
                    status = {"status_raw": status_raw}
            else:
                status = {"status_raw": status_raw}
        status["source"] = "replay"
        return Acquisition(freq_hz=freq, trace_dbm=trace, status=status)

    def _load_json(self, path: Path) -> Acquisition:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        freq = np.array(payload["freq_hz"], dtype=float)
        trace = np.array(payload["trace_dbm"], dtype=float)
        status = dict(payload.get("status") or {})
        status["source"] = "replay"
        return Acquisition(freq_hz=freq, trace_dbm=trace, status=status)
