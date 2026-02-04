"""Data models for monitoring results."""

from dataclasses import dataclass, field
from datetime import datetime

from src.config.constants import ProcessHealth


@dataclass
class CheckResult:
    process_key: str
    display_name: str
    health: ProcessHealth
    pid: int | None
    last_heartbeat: datetime | None
    elapsed_seconds: float | None
    timeout_seconds: float


@dataclass
class MonitorReport:
    timestamp: datetime
    results: list[CheckResult] = field(default_factory=list)

    @property
    def processes_checked(self) -> int:
        return len(self.results)

    @property
    def processes_healthy(self) -> int:
        return sum(
            1 for r in self.results if r.health == ProcessHealth.HEALTHY
        )

    @property
    def processes_unhealthy(self) -> int:
        return self.processes_checked - self.processes_healthy
