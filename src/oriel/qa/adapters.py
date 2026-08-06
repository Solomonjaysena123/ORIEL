"""Extension contracts for specialized QA integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class CheckRequest:
    target: str
    options: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CheckResult:
    passed: bool
    message: str = ""
    metrics: Mapping[str, float] = field(default_factory=dict)


class QAAdapter(ABC):
    domain = "generic"

    @abstractmethod
    def check(self, request: CheckRequest) -> CheckResult:
        """Execute one domain-specific check."""


class UnsupportedAdapter(QAAdapter):
    def check(self, request: CheckRequest) -> CheckResult:
        raise NotImplementedError(f"{self.domain} testing requires a configured provider adapter")
