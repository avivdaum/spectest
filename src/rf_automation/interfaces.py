from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import Acquisition, TestCase


class TxAdapterError(RuntimeError):
    """Raised when TX adapter operations fail."""


class RsaClientError(RuntimeError):
    """Raised when RSA operations fail."""


class TxAdapter(ABC):
    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def start_case(self, case: TestCase) -> None:
        raise NotImplementedError

    @abstractmethod
    def wait_ready(self, timeout_s: float) -> bool:
        raise NotImplementedError

    @abstractmethod
    def stop_case(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError


class RsaClient(ABC):
    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def preset(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def configure_spectrum(self, case: TestCase) -> None:
        raise NotImplementedError

    @abstractmethod
    def acquire_trace(self, timeout_ms: int) -> Acquisition:
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError
