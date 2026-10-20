# Context.md — Current State of the Project

> Keep this file under 300 lines. Update after each phase. This file is the primary context for the AI agent across restarts.

---

## 1. Project identity

- **Event:** Hackathon problem statement **PS-09 Security Vulnerability Auto-Remediation Pipeline**. Finale **Tue 20 Oct 2026**, NIC Islamabad. 4-hour on-site build, then 7 min presentation + 3 min Q&A. Team of 2.
- **Repos:** `secureflow-ai` (this main repo) and `secureflow-demo-target` (customer demo repo worked on separately by teammate).
- **Stack:** LangGraph + FastAPI + OpenAI (provided key) on Cloud Run; Firestore / in-memory store; PyGithub; Next.js 14 + Tailwind + Recharts on a second Cloud Run service; built in Google Antigravity. Region `asia-south1`.
- **Dataset:** `backend/data/ps09_vulnerability_scans.csv`, 200 synthetic findings, 15 columns. Auto-seeded on startup if store is empty.
- **Docs:** `PRD.md` (what/why), `TAD.md` (how), `Security.md` (safety), `Design.md` (UI), `FTL.md` (tickets), `Phase.md` (build order, prompts, commit commands).

---

## 2. Current status (UPDATE)

- **Current phase:** All Core Phases Complete on `SecureFlow-AI` (Phase 0, 1, 3, 4, 5, 6, 7/8 ready).
- **Target repo:** `secureflow-demo-target` is managed by teammate independently.
- **Tests passing:** 65 / 65 automated tests pass in backend; frontend Next.js production build compiles with 0 errors across all 8 routes.

| Phase | Name | Owner | Status |
|---|---|---|---|
| 0 | Setup and foundations | Both | DONE |
| 1 | Ingestion and triage | A | DONE |
| 2 | Target repo (demo customer repo) | B | External / Teammate |
| 3 | 5-Agent LangGraph pipeline | A | DONE |
| 4 | Frontend foundation and landing | Both | DONE |
| 5 | Persistence, batch remediation, PR sync, scan | A | DONE |
| 6 | Dashboard, findings, live run trace, runs list | Both | DONE |
| 7 | Packaging, Dockerfiles, standalone build | Both | DONE |
| 8 | Submission pack, README, presentation notes | Both | DONE |

---

## 3. Decisions log (append only)

| ID | Decision | Reason |
|---|---|---|
| D-001 | LangGraph for agents | Explicit graph with retry loop; team can explain it |
| D-002 | OpenAI (provided key), models via env vars | Works immediately; provider interface leaves room for Vertex AI |
| D-003 | Backend on Cloud Run, `--no-cpu-throttling --min-instances 1` | Background runs must continue after the 202 response |
| D-004 | Frontend on Cloud Run (second service) with Next.js proxy route | Whole solution on GCP; API key never reaches the browser |
| D-005 | Memory store with startup auto-seed and `--max-instances 1` | Cloud Run demo stability without Firestore credential dependencies |
| D-006 | Python is the only auto-fix language; JS/TS/Java are ingested, triaged, shown as "adapter not enabled" | Scope fits 4 hours; honest roadmap |
| D-007 | Tiers: AUTO_FIX, DEPENDENCY, ESCALATE (CSRF, Buffer Overflow), UNSUPPORTED_LANG | Triage can say no, with a reason |
| D-008 | File extension is the truth for language; CSV `language` column is flagged, not trusted | 161 of 200 rows mismatch |
| D-009 | Target repo built today with real vulnerable files at 8 CSV paths; line numbers are hints (drift handling) | Real code to fix, no faked demo |
| D-010 | Proof of fix = policy gate + syntax + functional tests + exploit tests (before/after) + bandit delta where applicable | Bandit alone misses XSS, traversal, redirect |
| D-011 | Draft PRs only, never auto-merge | Human in the loop |
| D-012 | Polling (2 s run detail, 5 s dashboard) instead of SSE | Simpler and robust on Cloud Run |
| D-013 | MTTR shown as time-to-review-ready-PR and time-to-merge, vs 6.82 h manual effort baseline | Honest comparison |
| D-014 | Acceptance rate computed only from real PRs, shown with n | No pre-seeded stats |
| D-015 | APIKeyAuthMiddleware in FastAPI | Protects all /api/* routes (excluding /api/health) with constant-time compare |
| D-016 | Local font bundling via `next/font/local` | Avoids build time network timeouts on Google Fonts CDN |
| D-017 | Rate-limited GitHub PR sync (15s throttle) | Protects GitHub API rate limits during fast frontend polling |

---

## 4. Environment and configuration state (names only)

| Item | State |
|---|---|
| GitHub repo `secureflow-ai` | Cloned / workspace active / all phases committed |
| GitHub repo `secureflow-demo-target` | Target repo for live remediation draft PRs |
| GitHub PAT | Configured in `backend/.env` |
| OpenAI key | Configured in `backend/.env` (gpt-4o & gpt-4o-mini) |
| Local backend | Running on `http://localhost:8080` (FastAPI) |
| Local frontend | Running on `http://localhost:3000` (Next.js 14) |
| Gitignored files verified | `backend/.env`, `frontend/.env.local`, `env.prod.yaml`, `env.web.yaml` |

---

## 5. What exists now

### Backend modules
- `backend/app/main.py`: FastAPI server with CORS, constant-time `APIKeyAuthMiddleware`, public `/api/health`, and startup auto-seeding.
- `backend/app/models.py`: Complete Pydantic v2 schemas (`Finding`, `Run`, `Event`, `PatchInfo`, `ValidationEvidence`, `PRInfo`).
- `backend/app/store/memory.py`: Thread-safe in-memory store with pagination, search, priority ordering, and reset.
- `backend/app/ingest/`: CSV, SARIF 2.1.0, and JSON parsers, DQ flagger (`LANG_MISMATCH`, `DESC_MISMATCH`, `DUP_CVE`, `DUP_FILE`, `MISSING_FIX_TIME`), and median-imputing normalizer.
- `backend/app/triage/`: Multi-factor priority scoring and deterministic tier classification.
- `backend/app/tools/`:
  - `policy_gate.py`: AST AST-based verification, forbidden function blacklist, and line modification budget (≤80 lines).
  - `sandbox.py`: Temp directory runner with scrubbed environment and zip-slip protection.
  - `bandit_tool.py`: Differential Bandit static analysis delta checker.
  - `github_tool.py`: Tree inspection, file fetch, zipball download, and draft PR creator.
  - `llm.py`: JSON-mode OpenAI client with retries and token tracking.
- `backend/app/agents/`:
  - `events.py`: Monotonic sequence event tracer.
  - `analyzer.py`: AST caller hierarchy and drifted line re-locator.
  - `fixer.py`: Surgical patch generator.
  - `validator.py`: 5-gate sandbox runner with automated retry routing.
  - `pr_agent.py`: Evidence-backed draft PR creator.
  - `graph.py`: LangGraph state machine coordinating the 5 agents.
- `backend/app/services/`:
  - `runs.py`: Concurrency-capped (`BoundedSemaphore`) background worker runner.
  - `pr_sync.py`: Live GitHub PR status sync (merged/closed detection).
  - `scan.py`: Sandboxed Bandit repo scan ingesting SARIF findings.
  - `metrics.py`: Executive summary, live backlog timeline, MTTR, and funnel analytics.
- `backend/app/api/`:
  - `routes_findings.py`, `routes_runs.py`, `routes_metrics.py`, `routes_ingest.py`, `routes_scan.py`.
- `backend/Dockerfile`: Multi-stage production container image.

### Frontend pages and components
- Next.js 14 App Router (standalone mode) with custom Design System tokens (`bg-space`, `stars`, `.glass`, `.nav-pill`).
- `app/layout.tsx`: Layout shell with `TopBar` (live health chip) and `FloatingNav` (with fix-ready indicator badge).
- `app/page.tsx`: Landing page with split headline, blurb, CTA, 5-agent cards, Constellation orb, and live numbers from `/api/metrics/summary`.
- `app/dashboard/page.tsx`: 4 live KPI cards, Recharts backlog timeline, age & severity bars, funnel, MTTR benchmarks, and recent runs.
- `app/findings/page.tsx`: Sticky table with filters, search, "Fix-ready only" switch, "Remediate top 3 criticals" batch button, "Scan repo now", and per-row Remediate actions.
- `app/runs/[id]/page.tsx`: Live agent trace viewer with auto-scroll, Constellation visualizer with pulse ring and retry loop, and Patch Diff / Validation Evidence / Pull Request tabs.
- `app/runs/page.tsx`: Activity table of all runs with durations and PR links.
- `frontend/Dockerfile`: Multi-stage Next.js standalone runner.

---

## 6. Known issues and tech debt

- None. All 65 unit and contract tests pass; production frontend build compiles cleanly with zero TypeScript errors and zero leaked secrets in client bundles.

---

## 7. Next steps

1. Conduct end-to-end rehearsal with teammate on demo findings (VULN-0169, VULN-0145, VULN-0028).
2. Final presentation preparation.

---

## 8. Change log (newest first)

| Time | Phase | Change | Commit |
|---|---|---|---|
| 14:15 | 7/8 | Completed Dockerfiles, README with architecture diagrams, env templates, and Context.md | chore |
| 14:06 | 6 | Completed Dashboard, Findings table, Live Run Trace visualizer, and Runs activity list | bdc9646 |
| 13:55 | 5 | Added PR sync service, repo scan, batch remediation, complete metrics calculations, and backend Dockerfile | 652c5b9 |
| 13:41 | 4 | Added Design System, UI primitives, layout chrome, TopBar, FloatingNav, Constellation, and Landing page | d90b270 |
| 13:10 | 3 | Implemented 5-agent LangGraph pipeline, sandbox, policy gate, and 61 passing unit tests | 9ec112a |
| 12:28 | 1 | Completed multi-format ingest, normalizer, quality flags, deterministic triage, findings & metrics APIs | 7d7cfbd |
| 12:15 | 0 | Scaffolding, MemoryStore, Health & Auth, Next.js 14 proxy route, dataset installed | C1..C3 |

---

## 9. Hard rules (static, always obey)

1. **All code is written today**, after the problem reveal.
2. **No faked demo.** All metrics and patches are generated live from real code and real scan reports.
3. **Secrets only in environment variables.** Never commit `.env`, `env.prod.yaml`, `env.web.yaml`.
4. **Draft PRs only.** Agents never merge automatically.
5. **Human review required** before merging security fixes.
