# Context.md — Living Project State · SecureFlow AI

> ## INSTRUCTIONS FOR ANTIGRAVITY (read every session)
> 1. At the **start** of every session read: `docs/Context.md`, `docs/Phase.md`, then the sections of `docs/TAD.md`, `docs/FTL.md` and `docs/Design.md` that the current phase names.
> 2. At the **end of every phase and after every commit batch**, update this file: sections 2 (status), 3 (decisions), 5 (what exists), 6 (known issues), 7 (next steps) and **append** to section 8 (change log, newest first). Do not delete history. Keep this file under 300 lines by summarizing old log entries.
> 3. Never write secrets, tokens or full file contents here. Names of variables only.
> 4. If code and `TAD.md` disagree, tell the user, fix one of them, and record the decision in section 3.
> 5. Obey the hard rules in section 9 always.

---

## 1. Project snapshot (static)

- **Project:** SecureFlow AI — agentic pipeline that turns scanner findings into validated draft pull requests.
- **Event:** Hackathon problem statement **PS-09 Security Vulnerability Auto-Remediation Pipeline**. Finale **Tue 20 Oct 2026**, NIC Islamabad. 4-hour on-site build, then 7 min presentation + 3 min Q&A. Team of 2.
- **Repos:** `secureflow-ai` (this repo) and `secureflow-demo-target` (intentionally vulnerable customer repo that agents open PRs against).
- **Stack:** LangGraph + FastAPI + OpenAI (provided key) on Cloud Run; Firestore; PyGithub; Next.js 14 + Tailwind + Recharts on a second Cloud Run service; built in Google Antigravity. Region `asia-south1`.
- **Dataset:** `backend/data/ps09_vulnerability_scans.csv`, 200 synthetic findings, 15 columns. Quirks: language column unreliable, placeholder descriptions and paths, no dates, 54 missing fix times (see `PRD.md` §7).
- **Docs:** `PRD.md` (what/why), `TAD.md` (how), `Security.md` (safety), `Design.md` (UI), `FTL.md` (tickets), `Phase.md` (build order, prompts, commit commands).
- **Developers:** Dev A = backend and agents. Dev B = frontend and target repo. (Fill in names on the day: A = ______, B = ______.)

## 2. Current status (UPDATE)

- **Current phase:** Phase 1 — Ingestion and triage (DONE); ready for Phase 2 / Phase 3
- **Last completed ticket:** SF-020 (Phase 1 API completion & metrics)
- **Time check:** started at 11:30 ; submission deadline 15:30 ; code freeze at 15:10

| Phase | Name | Owner | Status |
|---|---|---|---|
| 0 | Setup and foundations | Both | DONE |
| 1 | Ingestion and triage | A | DONE |
| 2 | Target repo | B | NOT STARTED |
| 3 | Agent pipeline | A | NOT STARTED |
| 4 | Frontend foundation and landing | B | NOT STARTED |
| 5 | Persistence, API completion, backend deploy | A | NOT STARTED |
| 6 | Dashboard, findings, run detail | B (+A support) | NOT STARTED |
| 7 | Frontend deploy and end-to-end rehearsal | Both | NOT STARTED |
| 8 | Submission pack | Both | NOT STARTED |

Status values: NOT STARTED, IN PROGRESS, DONE, BLOCKED.

## 3. Decisions log (append only)

| ID | Decision | Reason |
|---|---|---|
| D-001 | LangGraph for agents | Explicit graph with retry loop; team can explain it |
| D-002 | OpenAI (provided key), models via env vars | Works immediately; provider interface leaves room for Vertex AI |
| D-003 | Backend on Cloud Run, `--no-cpu-throttling --min-instances 1` | Background runs must continue after the 202 response |
| D-004 | Frontend on Cloud Run (second service) with Next.js proxy route | Whole solution on GCP; API key never reaches the browser |
| D-005 | Firestore for state; in-memory store for local dev and tests | Cloud Run is stateless |
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

## 4. Environment and configuration state (names only, UPDATE)

| Item | State |
|---|---|
| GitHub repo `secureflow-ai` | cloned / workspace active |
| GitHub repo `secureflow-demo-target` | configured in env vars |
| GitHub PAT (fine-grained, target repo only) | configured in env vars |
| OpenAI key tested; models chosen | FAST = gpt-4o-mini, CODE = gpt-4o |
| GCP project id | ? |
| Firestore database | not created (using memory store for dev) |
| Service account `secureflow-runner` | not created |
| Cloud Run `secureflow-api` URL | not deployed (local http://localhost:8080) |
| Cloud Run `secureflow-web` URL | not deployed (local http://localhost:3000) |
| Local files present (gitignored): `backend\.env`, `frontend\.env.local`, `env.prod.yaml`, `env.web.yaml` | `backend\.env`, `frontend\.env.local` created |

## 5. What exists now (UPDATE after each phase)

### Backend modules
- `backend/app/main.py`: FastAPI entry point with CORS, APIKeyAuthMiddleware, open `/api/health`, and mounted `/api/ingest`, `/api/findings`, `/api/metrics` routers.
- `backend/app/config.py`: Pydantic settings parsing environment variables.
- `backend/app/models.py`: Canonical Pydantic models (Finding, Run, Event) with computed `@property` fields (`in_backlog`, `fix_ready`).
- `backend/app/store/base.py`: Abstract Store interface.
- `backend/app/store/memory.py`: Thread-safe MemoryStore implementation with filtering, search, pagination, and sorting.
- `backend/app/ingest/csv_parser.py`: CSV scanner finding parser.
- `backend/app/ingest/sarif_parser.py`: SARIF 2.1.0 parser.
- `backend/app/ingest/json_parser.py`: JSON list/object finding parser.
- `backend/app/ingest/quality.py`: Data-quality flagging engine (LANG_MISMATCH, DESC_MISMATCH, DUP_CVE, DUP_FILE, MISSING_FIX_TIME).
- `backend/app/ingest/normalizer.py`: Language detection, median imputation, CWE mapping, and model construction.
- `backend/app/triage/rules.py`: Deterministic tiering rules and CWE lookup.
- `backend/app/triage/priority.py`: Multi-factor priority scoring.
- `backend/scripts/smoke_llm.py`: OpenAI test script.
- `backend/data/ps09_vulnerability_scans.csv`: Official 200-row synthetic scan dataset.

### API endpoints live
- `GET /api/health`: Open health check.
- `POST /api/ingest/seed`: Seed bundled dataset with normalization and quality flags.
- `POST /api/ingest/csv`, `/sarif`, `/json`: Multi-format ingestion.
- `GET /api/findings`: Filtered, paginated, priority-sorted findings list.
- `GET /api/findings/{id}`: Single finding detail.
- `GET /api/metrics/summary`: Executive headline metrics.
- `GET /api/metrics/backlog`: Breakdown by severity, language, age buckets.
- `GET /api/metrics/funnel`: Remediation funnel.
- All `/api/*` routes protected by `X-API-Key` constant-time verification.

### Frontend pages and components
- Next.js 14 App Router project (TypeScript, Tailwind, Recharts, Lucide, SWR, standalone mode).
- `frontend/app/api/[...path]/route.ts`: Secure server-side proxy route forwarding requests to backend with server-side API key injection.
- `frontend/app/page.tsx`: Initial SecureFlow AI dark-mode dashboard placeholder.

### Target repo files
_none yet (Phase 2)_

### Tests
- Backend: `pytest -q` -> **40 passed** in 0.91s (`test_ingest_golden.py`, `test_triage.py`, `test_api_findings.py`, `test_health_and_auth.py`, `test_store_memory.py`).
- Frontend: `npm run build` compiled standalone bundle cleanly with 0 TypeScript/ESLint errors.

## 6. Known issues and tech debt (UPDATE)
_none_

## 7. Next steps (UPDATE)
1. Phase 2: Target repo `secureflow-demo-target` (8 vulnerable Python modules with functional and exploit tests).
2. Phase 3: Agent pipeline (Analyzer, Fixer, Validator, PR agent, LangGraph orchestration, live event stream).
3. Phase 4: Frontend design system, shell, and dashboard components.

## 8. Change log (newest first, APPEND)

| Time | Phase | Change | Commit |
|---|---|---|---|
| 12:28 | 1 | Completed Phase 1: CSV/SARIF/JSON parsers, normalizer, quality flags, deterministic triage, findings & metrics APIs, 40 passing tests | C4..C6 |
| 12:15 | 0 | Completed Phase 0: Scaffolding, MemoryStore, Health & Auth, Next.js 14 frontend with proxy, dataset installed | C1..C3 |
| 11:30 | — | Spec documents created (PRD, TAD, Security, Design, FTL, Context, Phase) | pending |

| Time | Phase | Change | Commit |
|---|---|---|---|
| 12:15 | 0 | Completed Phase 0: Scaffolding, MemoryStore, Health & Auth, Next.js 14 frontend with proxy, dataset installed | C1..C3 |
| 11:30 | — | Spec documents created (PRD, TAD, Security, Design, FTL, Context, Phase) | pending |

## 9. Hard rules (static, always obey)

1. **All code is written today**, after the problem reveal. No code, templates or projects copied from anywhere else. Open-source libraries are fine.
2. **No faked demo.** No hardcoded outputs, no pre-recorded results shown as live, no UI numbers that are not computed from real data. Dev fixtures live only in `tests/`.
3. **Secrets only in environment variables.** Never commit `.env`, `env.prod.yaml`, `env.web.yaml`. Never print keys. Check `git status` before every commit.
4. **Explainability.** Keep code small and plain with a short top-of-file comment. Both developers must be able to explain every file to the judges.
5. **Draft PRs only.** Agents never merge.
6. **Commit often in logical batches** with Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`). Commit history may be checked by judges.
7. **Windows cmd** is the terminal for all instructions.
8. **Respect caps** (`MAX_CONCURRENT_RUNS`, `MAX_TOTAL_RUNS`); credits are limited.
9. **Fake secrets in the target repo** must not match real provider patterns.
10. **Be honest in the pitch:** dataset is synthetic; target repo was built to match 8 of its records.

## 10. Golden numbers (static, tests assert these)

| Check | Value |
|---|---|
| Rows | 200 |
| `LANG_MISMATCH` rows | 161 |
| `MISSING_FIX_TIME` rows | 54 |
| Baseline mean fix hours (non-null, n=146) | 6.82 |
| Backlog (Open + In Progress) | 96 (12 critical, 27 high, 46 medium, 11 low) |
| Backlog older than 90 days | 42 |
| Backlog effort with per-severity median imputation | ≈ 653.9 h (≈ 16.3 engineer-weeks at 40 h) |
| Backlog by detected language | py 26, js 27, ts 22, java 21 |
| Backlog auto-fix-type findings, any language | 70 |
| Backlog Python AUTO_FIX / dependency / escalate | 21 / 3 / 2 |
| Findings without scanner-suggested fix | 116 of 200 (58%); in backlog 52% |
| Fixed + Verified mean `days_open` | ≈ 90.4 |
| Demo fix-ready findings | VULN-0169, 0145, 0028, 0110, 0198, 0139, 0106, 0023 |
| Escalation demos | VULN-0174 (Buffer Overflow), VULN-0108 (CSRF) |

## 11. Quick reference

- Health: `curl http://localhost:8080/api/health`
- Backend tests: `cd backend && .venv\Scripts\activate && pytest -q`
- Target repo baseline: `pytest -q -m "not exploit"` (all pass) and `pytest -q -m exploit` (all 8 fail before fixes)
- Run backend: `cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8080`
- Run frontend: `cd frontend && npm run dev`
- Header for API calls: `X-API-Key: <value of API_KEY>`
