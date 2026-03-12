from __future__ import annotations

import ctypes
from ctypes import POINTER, byref, c_bool, c_double, c_float, c_int
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any

import numpy as np

from ..interfaces import RsaClient, RsaClientError
from ..models import Acquisition, TestCase

DEVSRCH_MAX_NUM_DEVICES = 20
DEVSRCH_SERIAL_MAX_STRLEN = 100
DEVSRCH_TYPE_MAX_STRLEN = 20


class SpectrumSettings(ctypes.Structure):
    _fields_ = [
        ("span", c_double),
        ("rbw", c_double),
        ("enableVBW", c_bool),
        ("vbw", c_double),
        ("traceLength", c_int),
        ("window", c_int),
        ("verticalUnit", c_int),
        ("actualStartFreq", c_double),
        ("actualStopFreq", c_double),
        ("actualFreqStepSize", c_double),
        ("actualRBW", c_double),
        ("actualVBW", c_double),
        ("actualNumIQSamples", c_double),
    ]


@dataclass
class LiveRsaClient(RsaClient):
    dll_path: str | None = None
    _dll: Any = None
    _connected: bool = False
    _settings: SpectrumSettings | None = None
    _status: dict[str, Any] = None

    def __post_init__(self) -> None:
        if self._status is None:
            self._status = {}
        self._load_dll()

    def _load_dll(self) -> None:
        try:
            if self.dll_path:
                path = str(Path(self.dll_path))
                self._dll = ctypes.WinDLL(path)
            else:
                self._dll = ctypes.WinDLL("RSA_API.dll")
        except Exception as exc:
            raise RsaClientError(f"Failed to load RSA API DLL: {exc}") from exc

    def connect(self) -> None:
        num_found = c_int(0)
        device_ids = (c_int * DEVSRCH_MAX_NUM_DEVICES)()
        device_serial = ctypes.create_string_buffer(DEVSRCH_SERIAL_MAX_STRLEN)
        device_type = ctypes.create_string_buffer(DEVSRCH_TYPE_MAX_STRLEN)
        self._call("DEVICE_Search", byref(num_found), device_ids, device_serial, device_type)
        if num_found.value < 1:
            raise RsaClientError("No RSA instruments found")
        self._call("DEVICE_Connect", device_ids[0])
        self._connected = True
        self._status = {
            "connected": True,
            "source": "live",
            "device_type": device_type.value.decode(errors="ignore"),
            "device_serial": device_serial.value.decode(errors="ignore"),
        }

    def preset(self) -> None:
        self._assert_connected()
        self._call("CONFIG_Preset")

    def configure_spectrum(self, case: TestCase) -> None:
        self._assert_connected()
        settings = SpectrumSettings()
        self._call("SPECTRUM_SetEnable", c_bool(True))
        self._call("CONFIG_SetCenterFreq", c_double(case.center_freq_hz))
        self._call("CONFIG_SetReferenceLevel", c_double(case.ref_level_dbm))
        self._call("SPECTRUM_SetDefault")
        self._call("SPECTRUM_GetSettings", byref(settings))
        settings.span = c_double(case.span_hz).value
        settings.rbw = c_double(case.rbw_hz).value
        self._call("SPECTRUM_SetSettings", settings)
        self._call("SPECTRUM_GetSettings", byref(settings))
        self._settings = settings

    def acquire_trace(self, timeout_ms: int) -> Acquisition:
        self._assert_connected()
        if self._settings is None:
            raise RsaClientError("Spectrum not configured before acquire_trace")
        ready = c_bool(False)
        timeout_s = timeout_ms / 1000.0
        trace_len = int(self._settings.traceLength)
        if trace_len <= 0:
            raise RsaClientError("Invalid trace length from RSA settings")
        trace_buffer = (c_float * trace_len)()
        out_points = c_int(0)
        deadline = monotonic() + timeout_s

        self._call("DEVICE_Run")
        self._call("SPECTRUM_AcquireTrace")
        while not ready.value and monotonic() < deadline:
            rs = self._dll.SPECTRUM_WaitForDataReady(c_int(100), byref(ready))
            if rs not in (0, 304):  # 304 -> data not ready
                raise RsaClientError(f"SPECTRUM_WaitForDataReady failed with code {rs}")
        if not ready.value:
            self._call("DEVICE_Stop")
            raise RsaClientError(f"Timed out waiting for spectrum trace ({timeout_ms} ms)")

        self._call(
            "SPECTRUM_GetTrace",
            c_int(0),
            c_int(trace_len),
            byref(trace_buffer),
            byref(out_points),
        )
        self._call("DEVICE_Stop")
        trace = np.ctypeslib.as_array(trace_buffer).astype(float)
        freq = np.arange(
            self._settings.actualStartFreq,
            self._settings.actualStartFreq + self._settings.actualFreqStepSize * trace_len,
            self._settings.actualFreqStepSize,
            dtype=float,
        )
        if len(freq) > trace_len:
            freq = freq[:trace_len]
        elif len(freq) < trace_len:
            freq = np.pad(freq, (0, trace_len - len(freq)), mode="edge")
        status = {
            "source": "live",
            "stable": True,
            "trace_points": int(out_points.value),
        }
        self._status = dict(status)
        self._status["connected"] = True
        return Acquisition(freq_hz=freq, trace_dbm=trace, status=status)

    def get_status(self) -> dict[str, Any]:
        return dict(self._status)

    def disconnect(self) -> None:
        if self._connected:
            try:
                self._call("DEVICE_Disconnect")
            finally:
                self._connected = False
                self._settings = None
                self._status = {"connected": False, "source": "live"}

    def _assert_connected(self) -> None:
        if not self._connected:
            raise RsaClientError("LiveRsaClient is not connected")

    def _call(self, fn_name: str, *args: Any) -> int:
        fn = getattr(self._dll, fn_name, None)
        if fn is None:
            raise RsaClientError(f"RSA API function not found: {fn_name}")
        rs = int(fn(*args))
        if rs != 0:
            raise RsaClientError(f"RSA API call {fn_name} failed with code {rs}")
        return rs

