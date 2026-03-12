from __future__ import annotations

import pytest

from rf_automation.clients.mock_rsa import MockRsaClient
from rf_automation.models import Limits, RunProfile, TestCase
from rf_automation.orchestrator import RFOrchestrator
from rf_automation.reporting import ReportWriter
from rf_automation.tx.null_tx import NullTxAdapter


@pytest.mark.rsa_only
def test_rsa_only_health_mode_passes_pipeline(tmp_path):
    case = TestCase(
        id="rsa_only_case",
        tx_mode="unused",
        center_freq_hz=2.4e9,
        span_hz=20e6,
        rbw_hz=10e3,
        ref_level_dbm=-20.0,
        limits=Limits(
            freq_error_hz_max=1.0,
            peak_power_dbm_min=100.0,
            peak_power_dbm_max=101.0,
            obw_hz_min=1.0,
            obw_hz_max=2.0,
        ),
    )
    profile = RunProfile(mode="rsa_only", reports_root=tmp_path / "reports")
    orchestrator = RFOrchestrator(
        tx_adapter=NullTxAdapter(),
        rsa_client=MockRsaClient(),
        report_writer=ReportWriter(profile.reports_root),
    )
    run = orchestrator.run(profile, [case])
    assert len(run.results) == 1
    assert run.results[0].passed is True
    assert run.results[0].limits is None
