from __future__ import annotations

from dataclasses import dataclass
from time import sleep

import numpy as np

from .clients.mock_rsa import MockRsaClient
from .clients.replay import ReplayTraceProvider
from .evaluator import effective_limits, evaluate_metrics
from .interfaces import RsaClient, RsaClientError, TxAdapter, TxAdapterError
from .metrics import compute_metrics
from .models import Acquisition, CaseResult, Limits, RunProfile, RunResult, TestCase
from .reporting import ReportWriter


@dataclass
class RFOrchestrator:
    tx_adapter: TxAdapter
    rsa_client: RsaClient
    report_writer: ReportWriter
    replay_provider: ReplayTraceProvider | None = None

    def run(self, profile: RunProfile, cases: list[TestCase]) -> RunResult:
        run_dir = self.report_writer.create_run_dir()
        run_id = run_dir.name
        results: list[CaseResult] = []
        mode = profile.mode
        mock_for_no_hw = (
            self.rsa_client
            if isinstance(self.rsa_client, MockRsaClient)
            else MockRsaClient(self.replay_provider)
        )

        try:
            if mode == "rsa_only":
                self.rsa_client.connect()
                self.rsa_client.preset()
            elif mode == "full_hw":
                self.tx_adapter.connect()
                self.rsa_client.connect()
                self.rsa_client.preset()

            for case in cases:
                result, acquisition = self._run_case(
                    mode, profile, case, mock_for_no_hw
                )
                result.artifacts = self.report_writer.write_case_artifacts(
                    run_dir, case, result, acquisition
                )
                results.append(result)
        finally:
            try:
                self.tx_adapter.disconnect()
            finally:
                self.rsa_client.disconnect()

        run_result = RunResult(
            run_id=run_id, mode=mode, results=results, report_dir=run_dir
        )
        self.report_writer.write_run_outputs(run_result)
        return run_result

    def _run_case(
        self,
        mode: str,
        profile: RunProfile,
        case: TestCase,
        mock_for_no_hw: MockRsaClient,
    ) -> tuple[CaseResult, Acquisition | None]:
        settle_ms = case.settle_ms if case.settle_ms is not None else profile.settle_ms
        max_retries = (
            case.max_retries if case.max_retries is not None else profile.max_retries
        )
        timeout_ms = profile.timeout_ms
        last_error: str | None = None
        acquisition: Acquisition | None = None

        for attempt in range(max_retries + 1):
            try:
                acquisition = self._acquire(
                    mode, case, settle_ms, timeout_ms, mock_for_no_hw
                )
                self._assert_stable(acquisition)
                metrics = compute_metrics(acquisition, case)
                if mode == "rsa_only":
                    passed, reasons = True, []
                    limits: Limits | None = None
                else:
                    limits = effective_limits(case)
                    passed, reasons = evaluate_metrics(metrics, limits)
                result = CaseResult(
                    case_id=case.id,
                    mode=mode,
                    passed=passed,
                    reasons=reasons,
                    retries_used=attempt,
                    metrics=metrics,
                    limits=limits,
                    acq_status=dict(acquisition.status),
                    error=None,
                )
                return result, acquisition
            except Exception as exc:
                last_error = str(exc)
                try:
                    self.tx_adapter.stop_case()
                except Exception:
                    pass
                if attempt >= max_retries:
                    break

        failure = CaseResult(
            case_id=case.id,
            mode=mode,
            passed=False,
            reasons=["acquisition_failed"],
            retries_used=max_retries,
            metrics=None,
            limits=effective_limits(case) if mode != "rsa_only" else None,
            acq_status={} if acquisition is None else dict(acquisition.status),
            error=last_error,
        )
        return failure, acquisition

    def _acquire(
        self,
        mode: str,
        case: TestCase,
        settle_ms: int,
        timeout_ms: int,
        mock_for_no_hw: MockRsaClient,
    ) -> Acquisition:
        if mode == "no_hardware":
            mock_for_no_hw.connect()
            mock_for_no_hw.configure_spectrum(case)
            sleep(settle_ms / 1000.0)
            return mock_for_no_hw.acquire_trace(timeout_ms)

        if mode == "rsa_only":
            self.rsa_client.configure_spectrum(case)
            sleep(settle_ms / 1000.0)
            return self.rsa_client.acquire_trace(timeout_ms)

        if mode == "full_hw":
            self.tx_adapter.start_case(case)
            if not self.tx_adapter.wait_ready(timeout_s=max(0.1, settle_ms / 1000.0)):
                raise TxAdapterError("TX adapter did not report ready")
            self.rsa_client.configure_spectrum(case)
            sleep(settle_ms / 1000.0)
            acq = self.rsa_client.acquire_trace(timeout_ms)
            self.tx_adapter.stop_case()
            return acq

        raise ValueError(f"Unsupported mode: {mode}")

    def _assert_stable(self, acquisition: Acquisition) -> None:
        if acquisition.freq_hz.size == 0 or acquisition.trace_dbm.size == 0:
            raise RsaClientError("empty acquisition")
        if acquisition.freq_hz.size != acquisition.trace_dbm.size:
            raise RsaClientError("freq/trace length mismatch")
        if bool(np.isnan(acquisition.trace_dbm).any()):
            raise RsaClientError("trace contains NaN values")
        if acquisition.status.get("stable") is False:
            raise RsaClientError("acquisition marked unstable by source")
        acq_status = acquisition.status.get("acq_status")
        if isinstance(acq_status, int) and acq_status != 0:
            raise RsaClientError(f"non-zero acquisition status: {acq_status}")
