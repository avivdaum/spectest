from __future__ import annotations

import json

import pytest

from rf_automation.config import load_cases, load_run_profile


@pytest.mark.unit
def test_load_cases(tmp_path):
    payload = [
        {
            "id": "c1",
            "tx_mode": "cw",
            "center_freq_hz": 100.0,
            "span_hz": 20.0,
            "rbw_hz": 1.0,
            "ref_level_dbm": -30.0,
            "limits": {"freq_error_hz_max": 5.0},
        }
    ]
    path = tmp_path / "cases.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    cases = load_cases(path)
    assert len(cases) == 1
    assert cases[0].id == "c1"
    assert cases[0].limits.freq_error_hz_max == 5.0


@pytest.mark.unit
def test_load_run_profile(tmp_path):
    payload = {"mode": "rsa_only", "settle_ms": 750}
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    profile = load_run_profile(path)
    assert profile.mode == "rsa_only"
    assert profile.settle_ms == 750

