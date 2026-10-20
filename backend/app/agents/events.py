# backend/app/agents/events.py
# Real-time event trace emitter. Persists ordered agent trace steps to the Store.

from __future__ import annotations

from typing import Any

from app.models import Event, EventLevel
from app.store import get_store


def emit(
    run_id: str,
    agent: str,
    message: str,
    level: EventLevel | str = EventLevel.info,
    data: dict[str, Any] | None = None,
) -> Event:
    """Emit an agent trace event with an atomically incremented sequence number."""
    store = get_store()
    seq = store.incr_counter(f"seq_{run_id}", 1)

    lvl = level if isinstance(level, EventLevel) else EventLevel(level)

    event = Event(
        run_id=run_id,
        seq=seq,
        agent=agent,
        level=lvl,
        message=message,
        data=data,
    )
    store.append_event(event)
    return event
