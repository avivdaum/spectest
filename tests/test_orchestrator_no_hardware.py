from __future__ import annotations

import numpy as np
import pytest

from rf_automation.clients.mock_rsa import MockRsaClient
from rf_automation.clients.replay import ReplayTraceProvider
from rf_automation.models import Limits, RunProfile, TestCase
from rf_automation.orchestrator import RFOrchestrator
from rf_automation.reporting import ReportWriter
from rf_automation.tx.null_tx import NullTxAdapter


@pytest.mark.no_hardware
def test_no_hardware_replay_then_synthetic_fallback(tmp_path):
    replay_root = tmp_path / "replay_data"
    replay_root.mkdir()
    freq = np.linspace(100.0, 200.0, 64)
    trace = np.linspace(-100.0, -20.0, 64)
    np.savez(replay_root / "case_replay.npz", freq_hz=freq, trace_dbm=trace)

    cases = [
        TestCase(
            id="case_replay",
            tx_mode="cw",
            center_freq_hz=150.0,
            span_hz=100.0,
            rbw_hz=1.0,
            ref_level_dbm=-10.0,
            limits=Limits(),
        ),
        TestCase(
            id="case_synth",
            tx_mode="cw",
            center_freq_hz=915e6,
            span_hz=5e6,
            rbw_hz=3e3,
            ref_level_dbm=-30.0,
            limits=Limits(),
        ),
    ]
    profile = RunProfile(
        mode="no_hardware",
        reports_root=tmp_path / "reports",
        replay_root=replay_root,
    )
    replay_provider = ReplayTraceProvider(replay_root)
    orchestrator = RFOrchestrator(
        tx_adapter=NullTxAdapter(),
        rsa_client=MockRsaClient(replay_provider),
        report_writer=ReportWriter(profile.reports_root),
        replay_provider=replay_provider,
    )
    run = orchestrator.run(profile, cases)
    assert len(run.results) == 2
    assert run.report_dir.exists()
    assert any(
        p.replace("\\", "/").endswith("cases/case_replay/trace.npz")
        for r in run.results
        for p in r.artifacts.values()
    )
