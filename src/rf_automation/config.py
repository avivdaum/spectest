from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import RunProfile, TestCase


def load_cases(path: str | Path) -> list[TestCase]:
    payload = _load_json(path)
    if not isinstance(payload, list):
        raise ValueError("cases file must be a JSON array")
    return [TestCase.from_dict(_expect_dict(item, "case")) for item in payload]


def load_run_profile(path: str | Path) -> RunProfile:
    payload = _load_json(path)
    return RunProfile.from_dict(_expect_dict(payload, "run_profile"))


def _load_json(path: str | Path) -> Any:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"JSON file not found: {p}")
    with p.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _expect_dict(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value

