from __future__ import annotations

from dataclasses import dataclass

from ..interfaces import TxAdapter
from ..models import TestCase


@dataclass
class NullTxAdapter(TxAdapter):
    """No-op TX adapter for no_hardware and rsa_only modes."""

    connected: bool = False

    def connect(self) -> None:
        self.connected = True

    def start_case(self, case: TestCase) -> None:
        del case

    def wait_ready(self, timeout_s: float) -> bool:
        del timeout_s
        return True

    def stop_case(self) -> None:
        return None

    def disconnect(self) -> None:
        self.connected = False

