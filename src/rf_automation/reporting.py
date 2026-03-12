from __future__ import annotations

import csv
import json
from base64 import b64decode
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .models import Acquisition, CaseResult, RunResult, TestCase

_PLACEHOLDER_PNG = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
)


class ReportWriter:
    def __init__(self, reports_root: str | Path):
        self.reports_root = Path(reports_root)

    def create_run_dir(self) -> Path:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_dir = self.reports_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def write_case_artifacts(
        self,
        run_dir: Path,
        case: TestCase,
        result: CaseResult,
        acquisition: Acquisition | None,
    ) -> dict[str, str]:
        case_dir = run_dir / "cases" / case.id
        case_dir.mkdir(parents=True, exist_ok=True)
        artifacts: dict[str, str] = {}

        result_path = case_dir / "result.json"
        with result_path.open("w", encoding="utf-8") as handle:
            json.dump(result.to_dict(), handle, indent=2)
        artifacts["result_json"] = str(result_path)

        if acquisition is not None:
            npz_path = case_dir / "trace.npz"
            np.savez(
                npz_path,
                freq_hz=acquisition.freq_hz,
                trace_dbm=acquisition.trace_dbm,
                status_json=json.dumps(acquisition.status),
            )
            artifacts["trace_npz"] = str(npz_path)

            plot_path = case_dir / "trace_plot.png"
            self._write_plot(plot_path, acquisition)
            artifacts["trace_plot"] = str(plot_path)

        return artifacts

    def write_run_outputs(self, run_result: RunResult) -> None:
        self._write_summary_csv(run_result)
        self._write_html_report(run_result)

    def _write_summary_csv(self, run_result: RunResult) -> None:
        path = run_result.report_dir / "summary.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "case_id",
                    "mode",
                    "passed",
                    "retries_used",
                    "peak_power_dbm",
                    "peak_freq_hz",
                    "freq_error_hz",
                    "occupied_bw_hz",
                    "reasons",
                    "error",
                ]
            )
            for result in run_result.results:
                metrics = result.metrics
                writer.writerow(
                    [
                        result.case_id,
                        result.mode,
                        result.passed,
                        result.retries_used,
                        "" if metrics is None else f"{metrics.peak_power_dbm:.6f}",
                        "" if metrics is None else f"{metrics.peak_freq_hz:.6f}",
                        "" if metrics is None else f"{metrics.freq_error_hz:.6f}",
                        "" if metrics is None else f"{metrics.occupied_bw_hz:.6f}",
                        "; ".join(result.reasons),
                        result.error or "",
                    ]
                )

    def _write_html_report(self, run_result: RunResult) -> None:
        path = run_result.report_dir / "report.html"
        rows = []
        for result in run_result.results:
            metrics = result.metrics
            plot_link = _link_for_artifact(
                run_result.report_dir, result.artifacts.get("trace_plot")
            )
            npz_link = _link_for_artifact(
                run_result.report_dir, result.artifacts.get("trace_npz")
            )
            rows.append(
                "<tr>"
                f"<td>{result.case_id}</td>"
                f"<td>{'PASS' if result.passed else 'FAIL'}</td>"
                f"<td>{result.retries_used}</td>"
                f"<td>{'' if metrics is None else f'{metrics.peak_power_dbm:.3f}'}</td>"
                f"<td>{'' if metrics is None else f'{metrics.peak_freq_hz:.3f}'}</td>"
                f"<td>{'' if metrics is None else f'{metrics.freq_error_hz:.3f}'}</td>"
                f"<td>{'' if metrics is None else f'{metrics.occupied_bw_hz:.3f}'}</td>"
                f"<td>{', '.join(result.reasons)}</td>"
                f"<td>{plot_link}</td>"
                f"<td>{npz_link}</td>"
                "</tr>"
            )
        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>RF Automation Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 1.5rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 0.4rem; font-size: 0.9rem; }}
    th {{ background: #f4f4f4; }}
  </style>
</head>
<body>
  <h1>RF Automation Report</h1>
  <p>Run ID: {run_result.run_id}</p>
  <p>Mode: {run_result.mode}</p>
  <p>Passed: {run_result.passed} | Failed: {run_result.failed}</p>
  <table>
    <thead>
      <tr>
        <th>Case</th><th>Verdict</th><th>Retries</th><th>Peak Power (dBm)</th>
        <th>Peak Freq (Hz)</th><th>Freq Error (Hz)</th><th>OBW (Hz)</th>
        <th>Reasons</th><th>Plot</th><th>Trace</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body>
</html>"""
        with path.open("w", encoding="utf-8") as handle:
            handle.write(html)

    def _write_plot(self, path: Path, acquisition: Acquisition) -> None:
        try:
            import matplotlib.pyplot as plt

            plt.figure(figsize=(10, 4))
            plt.plot(acquisition.freq_hz, acquisition.trace_dbm, linewidth=1)
            plt.xlabel("Frequency (Hz)")
            plt.ylabel("Power (dBm)")
            plt.title("Spectrum Trace")
            plt.tight_layout()
            plt.savefig(path)
            plt.close()
        except Exception:
            path.write_bytes(_PLACEHOLDER_PNG)


def _link_for_artifact(run_dir: Path, artifact_path: str | None) -> str:
    if not artifact_path:
        return ""
    path = Path(artifact_path)
    rel = path.relative_to(run_dir)
    return f'<a href="{rel.as_posix()}">{rel.name}</a>'
