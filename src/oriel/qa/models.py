"""Serializable QA result model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Attempt:
    status: str
    duration: float
    message: str = ""


@dataclass
class TestResult:
    test_id: str
    category: str = "unit"
    attempts: list[Attempt] = field(default_factory=list)

    @property
    def status(self) -> str:
        return self.attempts[-1].status

    @property
    def duration(self) -> float:
        return sum(a.duration for a in self.attempts)

    @property
    def flaky(self) -> bool:
        return self.status == "passed" and any(a.status != "passed" for a in self.attempts[:-1])


@dataclass
class RunSummary:
    results: list[TestResult]
    duration: float
    coverage: dict[str, float] = field(default_factory=dict)

    @property
    def passed(self) -> int:
        return sum(r.status == "passed" for r in self.results)

    @property
    def failed(self) -> int:
        return sum(r.status in {"failed", "error"} for r in self.results)

    @property
    def skipped(self) -> int:
        return sum(r.status == "skipped" for r in self.results)

    @property
    def flaky(self) -> int:
        return sum(r.flaky for r in self.results)

    @property
    def successful(self) -> bool:
        return self.failed == 0

    @property
    def coverage_total(self) -> float | None:
        """Return an unweighted mean for collected file coverage."""
        if not self.coverage:
            return None
        return round(sum(self.coverage.values()) / len(self.coverage), 2)
