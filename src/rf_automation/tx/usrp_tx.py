from __future__ import annotations

import importlib
from dataclasses import asdict, dataclass
from types import ModuleType
from typing import Any, Callable

from ..interfaces import TxAdapter, TxAdapterError
from ..models import TestCase


@dataclass
class UsrpTxAdapter(TxAdapter):
    """
    Adapter that bridges to user-supplied USRP TX module hooks.

    Expected module callables:
    - connect() -> None
    - start_case(case: dict) -> None
    - wait_ready(timeout_s: float) -> bool
    - stop_case() -> None
    - disconnect() -> None
    """

    module_path: str | None = None
    _module: ModuleType | None = None

    def connect(self) -> None:
        self._ensure_module()
        self._call("connect")

    def start_case(self, case: TestCase) -> None:
        self._ensure_module()
        self._call("start_case", asdict(case))

    def wait_ready(self, timeout_s: float) -> bool:
        self._ensure_module()
        result = self._call("wait_ready", timeout_s)
        return bool(result)

    def stop_case(self) -> None:
        self._ensure_module()
        self._call("stop_case")

    def disconnect(self) -> None:
        if self._module is None:
            return
        self._call("disconnect")

    def _ensure_module(self) -> None:
        if self._module is not None:
            return
        if not self.module_path:
            raise TxAdapterError(
                "UsrpTxAdapter requires module_path. "
                "Provide a Python module with connect/start_case/wait_ready/stop_case/disconnect."
            )
        try:
            self._module = importlib.import_module(self.module_path)
        except Exception as exc:
            raise TxAdapterError(f"Failed to import TX module {self.module_path}: {exc}") from exc

    def _call(self, name: str, *args: Any) -> Any:
        if self._module is None:
            raise TxAdapterError("TX module is not loaded")
        fn = getattr(self._module, name, None)
        if fn is None or not callable(fn):
            raise TxAdapterError(f"TX module is missing callable: {name}")
        try:
            return fn(*args)
        except Exception as exc:
            raise TxAdapterError(f"TX module {name} failed: {exc}") from exc
