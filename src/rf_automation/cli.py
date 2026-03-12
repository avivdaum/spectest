from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .clients import LiveRsaClient, MockRsaClient, ReplayTraceProvider
from .config import load_cases, load_run_profile
from .interfaces import RsaClient, TxAdapter
from .models import RunProfile
from .orchestrator import RFOrchestrator
from .reporting import ReportWriter
from .tx import NullTxAdapter, UsrpTxAdapter


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    profile = load_run_profile(args.profile)
    if args.mode:
        profile.mode = args.mode
    if args.reports_root:
        profile.reports_root = Path(args.reports_root)
    if args.replay_root:
        profile.replay_root = Path(args.replay_root)
    if args.rsa_dll_path:
        profile.rsa_dll_path = args.rsa_dll_path
    cases = load_cases(args.cases)

    tx_adapter, rsa_client, replay_provider = build_runtime_clients(
        profile, args.tx_module
    )
    orchestrator = RFOrchestrator(
        tx_adapter=tx_adapter,
        rsa_client=rsa_client,
        report_writer=ReportWriter(profile.reports_root),
        replay_provider=replay_provider,
    )
    run_result = orchestrator.run(profile, cases)
    print(json.dumps(_run_summary(run_result), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="USRP + RSA RF automation runner")
    parser.add_argument(
        "--profile", default="configs/run_profile.json", help="Path to run profile JSON"
    )
    parser.add_argument(
        "--cases", default="configs/cases.json", help="Path to cases JSON"
    )
    parser.add_argument(
        "--mode", choices=["no_hardware", "rsa_only", "full_hw"], help="Override mode"
    )
    parser.add_argument("--reports-root", help="Override reports root folder")
    parser.add_argument("--replay-root", help="Override replay root folder")
    parser.add_argument("--rsa-dll-path", help="Path to RSA_API.dll")
    parser.add_argument(
        "--tx-module", help="Python module path implementing TX hooks for full_hw mode"
    )
    return parser


def build_runtime_clients(
    profile: RunProfile, tx_module: str | None
) -> tuple[TxAdapter, RsaClient, ReplayTraceProvider]:
    replay_provider = ReplayTraceProvider(profile.replay_root)
    if profile.mode == "no_hardware":
        return NullTxAdapter(), MockRsaClient(replay_provider), replay_provider
    if profile.mode == "rsa_only":
        return (
            NullTxAdapter(),
            LiveRsaClient(dll_path=profile.rsa_dll_path),
            replay_provider,
        )
    if profile.mode == "full_hw":
        return (
            UsrpTxAdapter(module_path=tx_module),
            LiveRsaClient(dll_path=profile.rsa_dll_path),
            replay_provider,
        )
    raise ValueError(f"Unsupported mode: {profile.mode}")


def _run_summary(run_result: Any) -> dict[str, Any]:
    return {
        "run_id": run_result.run_id,
        "mode": run_result.mode,
        "report_dir": str(run_result.report_dir),
        "passed": run_result.passed,
        "failed": run_result.failed,
        "total": len(run_result.results),
    }
