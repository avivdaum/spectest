from __future__ import annotations

from dataclasses import dataclass

import pytest

from rf_automation.clients.mock_rsa import MockRsaClient
from rf_automation.interfaces import TxAdapter
from rf_automation.models import Limits, RunProfile, TestCase
from rf_automation.orchestrator import RFOrchestrator
from rf_automation.reporting import ReportWriter


@dataclass
class FakeTxAdapter(TxAdapter):
    connected: bool = False
    starts: int = 0
    stops: int = 0

    def connect(self) -> None:
        self.connected = True

    def start_case(self, case: TestCase) -> None:
        del case
        self.starts += 1

    def wait_ready(self, timeout_s: float) -> bool:
        del timeout_s
        return True

    def stop_case(self) -> None:
        self.stops += 1

    def disconnect(self) -> None:
        self.connected = False


@pytest.mark.full_hw
def test_full_hw_mode_runs_end_to_end_with_mocked_clients(tmp_path):
    tx = FakeTxAdapter()
    rsa = MockRsaClient()
    case = TestCase(
        id="full_hw_case",
        tx_mode="ofdm",
        center_freq_hz=915e6,
        span_hz=10e6,
        rbw_hz=10e3,
        ref_level_dbm=-15.0,
        limits=Limits(
            freq_error_hz_max=5e6,
            peak_power_dbm_min=-90.0,
            peak_power_dbm_max=5.0,
            obw_hz_min=1e3,
            obw_hz_max=10e6,
        ),
    )
    profile = RunProfile(mode="full_hw", reports_root=tmp_path / "reports")
    orchestrator = RFOrchestrator(
        tx_adapter=tx,
        rsa_client=rsa,
        report_writer=ReportWriter(profile.reports_root),
    )
    run = orchestrator.run(profile, [case])
    assert len(run.results) == 1
    assert tx.starts == 1
    assert tx.stops == 1
    assert run.results[0].metrics is not None
