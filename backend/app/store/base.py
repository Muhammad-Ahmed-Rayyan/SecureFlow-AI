# store/base.py — abstract Store interface used by both in-memory and Firestore backends.
# All methods are synchronous; the background thread calls them directly.

from abc import ABC, abstractmethod
from typing import Any, Optional
from app.models import Finding, Run, Event


class Store(ABC):
    """Interface that every persistence backend must implement."""

    # --- Findings ---

    @abstractmethod
    def upsert_finding(self, finding: Finding) -> None:
        """Insert or fully replace a finding by id."""

    @abstractmethod
    def get_finding(self, finding_id: str) -> Optional[Finding]:
        """Return a Finding or None."""

    @abstractmethod
    def update_finding(self, finding_id: str, **fields: Any) -> None:
        """Patch specific fields on an existing finding."""

    @abstractmethod
    def list_findings(self, filters: dict[str, Any]) -> list[Finding]:
        """Return filtered, sorted list of findings (priority_score desc)."""

    # --- Runs ---

    @abstractmethod
    def create_run(self, run: Run) -> None:
        """Persist a new Run document."""

    @abstractmethod
    def get_run(self, run_id: str) -> Optional[Run]:
        """Return a Run or None."""

    @abstractmethod
    def update_run(self, run_id: str, **fields: Any) -> None:
        """Patch specific fields on an existing run."""

    @abstractmethod
    def list_runs(self) -> list[Run]:
        """Return all runs, newest first."""

    # --- Events ---

    @abstractmethod
    def append_event(self, event: Event) -> None:
        """Append an Event; seq must be set by the caller."""

    @abstractmethod
    def list_events(self, run_id: str, after_seq: int = 0) -> list[Event]:
        """Return events for a run with seq > after_seq."""

    # --- Counters ---

    @abstractmethod
    def incr_counter(self, name: str, amount: int = 1) -> int:
        """Atomically increment a named counter and return the new value."""

    @abstractmethod
    def get_counter(self, name: str) -> int:
        """Return the current value of a named counter (0 if missing)."""
