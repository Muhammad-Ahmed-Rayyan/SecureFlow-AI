# main.py — FastAPI application entry point for SecureFlow AI backend.
# Registers CORS (frontend only), mounts all API routers, creates the store singleton.

import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from app.config import settings
from app.store import get_store
from app.store.base import Store


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise store on startup
    store = get_store()
    # Auto-seed ps09 CSV if store is empty
    findings = store.list_findings({"page": 1, "page_size": 1})
    if not findings:
        from pathlib import Path
        from app.ingest.csv_parser import parse_csv_content
        from app.ingest.normalizer import normalize_findings

        csv_path = Path(__file__).resolve().parent.parent / "data" / "ps09_vulnerability_scans.csv"
        if csv_path.exists():
            raw_text = csv_path.read_text(encoding="utf-8")
            raw_rows = parse_csv_content(raw_text)
            norm = normalize_findings(raw_rows)
            for f in norm:
                store.save_finding(f)
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SecureFlow AI",
    description="Agentic security vulnerability remediation pipeline — PS-09",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API-key authentication dependency and middleware
# ---------------------------------------------------------------------------

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Allow CORS preflight requests
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        # Health check is public for Cloud Run probes and UI status
        if path == "/api/health" or not path.startswith("/api"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key or not secrets.compare_digest(api_key, settings.api_key):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid X-API-Key header"},
            )

        return await call_next(request)


app.add_middleware(APIKeyAuthMiddleware)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Depends(_api_key_header)) -> str:
    """Dependency for explicit route injection if needed.

    Uses secrets.compare_digest to prevent timing attacks.
    """
    if not api_key or not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-API-Key header",
        )
    return api_key


# ---------------------------------------------------------------------------
# Health endpoint (no auth required)
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["meta"])
def health():
    """Open health check — used by the frontend TopBar and Cloud Run probes."""
    return {
        "status": "ok",
        "store": settings.store_backend,
        "version": "0.1.0",
    }


# ---------------------------------------------------------------------------
# Routers (mounted as they are built in later phases)
# ---------------------------------------------------------------------------

# Phase 1 — ingestion and findings
try:
    from app.api.routes_ingest import router as ingest_router
    from app.api.routes_findings import router as findings_router
    from app.api.routes_metrics import router as metrics_router
    app.include_router(ingest_router, prefix="/api", tags=["ingest"])
    app.include_router(findings_router, prefix="/api", tags=["findings"])
    app.include_router(metrics_router, prefix="/api", tags=["metrics"])
except ImportError:
    pass  # routers not yet implemented — Phase 0 only needs health + auth

# Phase 3 — runs and agents
from app.api.routes_runs import router as runs_router
app.include_router(runs_router, prefix="/api", tags=["runs"])

# Phase 5 — scan and PR sync
try:
    from app.api.routes_scan import router as scan_router
    app.include_router(scan_router, prefix="/api", tags=["scan"])
except ImportError:
    pass
