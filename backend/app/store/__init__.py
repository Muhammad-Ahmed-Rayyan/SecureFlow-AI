# store/__init__.py — exports the active store singleton chosen by STORE_BACKEND env var.

from __future__ import annotations

from app.config import settings
from app.store.base import Store
from app.store.memory import MemoryStore

_store: Store | None = None


def get_store() -> Store:
    """Return the global Store singleton (MemoryStore or FirestoreStore)."""
    global _store
    if _store is None:
        if settings.store_backend == "firestore":
            from app.store.firestore import FirestoreStore  # noqa: PLC0415
            _store = FirestoreStore()
        else:
            _store = MemoryStore()
    return _store
