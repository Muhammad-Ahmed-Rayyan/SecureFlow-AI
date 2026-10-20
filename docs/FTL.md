# FTL.md — Feature Ticket List · SecureFlow AI

> Every ticket has an owner, a priority, an estimate, acceptance criteria and a commit message. Work tickets in the order shown inside each phase. Mark status here as you go (`[ ]` → `[x]`) and mirror it in `Context.md`.

**Owners:** **A** = Backend and agents · **B** = Frontend and target repo · **Both** = pair up.
**Priority:** **P0** must ship · **P1** should ship · **P2** stretch (only if ahead of schedule).
**Estimates** are in minutes and assume Antigravity does the typing while you review and test.

Commit messages follow Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`). Commit by **logical batch** (several tickets in one commit when they belong together), never one file at a time. Batches are marked **[C1]**, **[C2]** … in each phase; `Phase.md` has the exact commands.

---

## Epic A — Foundation (Phase 0)

| ✓ | ID | Ticket | Owner | Pri | Est | Acceptance criteria |
|---|---|---|---|---|---|---|
| [ ] | SF-001 | Create GitHub repos `secureflow-ai` and `secureflow-demo-target`; create fine-grained PAT scoped to the target repo; clone both | Both | P0 | 10 | Both repos exist, cloned locally; PAT has only Contents RW, Pull requests RW, Metadata R on the target repo |
| [ ] | SF-002 | Add `docs/` (7 files), README skeleton, `.gitignore`, `.env.example`, folder structure | A | P0 | 5 | `git status` shows no secret files; first commit pushed **[C1]** |
| [ ] | SF-003 | Backend skeleton: FastAPI app, `config.py`, `/api/health`, API-key dependency, CORS | A | P0 | 15 | `curl /api/health` returns ok; other route without key returns 401 **[C2]** |
| [ ] | SF-004 | `Store` interface + in-memory implementation + models/enums | A | P0 | 10 | Contract tests pass for memory store |
| [ ] | SF-005 | Frontend scaffold: Next 14, Tailwind, fonts, `next.config.mjs` standalone, proxy route `app/api/[...path]/route.ts` | B | P0 | 15 | `npm run dev` renders a page; `/api/health` through the proxy returns backend health **[C3]** |
| [ ] | SF-006 | Check which OpenAI models the key supports; set `OPENAI_MODEL_FAST` and `OPENAI_MODEL_CODE`; smoke-call the API | A | P0 | 5 | One successful JSON-mode completion locally |

## Epic B — Ingestion and triage (Phase 1, Dev A)

| ✓ | ID | Ticket | Owner | Pri | Est | Acceptance criteria |
|---|---|---|---|---|---|---|
| [ ] | SF-010 | `Finding` model, enums, field aliases | A | P0 | 10 | Matches `TAD.md` §4.1 |
| [ ] | SF-011 | CSV parser (stdlib `csv`) | A | P0 | 10 | Parses all 200 rows of the bundled CSV |
| [ ] | SF-012 | SARIF parser (2.1.0) | A | P0 | 15 | Parses a bandit SARIF sample into findings with path, line, rule, severity |
| [ ] | SF-013 | JSON parser (array or `{findings: []}`) | A | P1 | 10 | Round-trips a normalized export |
| [ ] | SF-014 | Normalizer: language from extension, severity enum, vuln type normalization, per-severity median imputation | A | P0 | 15 | Golden numbers for fix hours and language counts pass **[C4]** |
| [ ] | SF-015 | Data-quality flags (`LANG_MISMATCH`, `DESC_MISMATCH`, `DUP_CVE`, `DUP_FILE`, `MISSING_FIX_TIME`) | A | P0 | 15 | 161 `LANG_MISMATCH`, 54 `MISSING_FIX_TIME` on bundled CSV |
| [ ] | SF-016 | Tiering rules, priority score, CWE map | A | P0 | 15 | Backlog: 70 auto-fix-type findings; 21 Python AUTO_FIX; CSRF and Buffer Overflow → ESCALATE **[C5]** |
| [ ] | SF-017 | LLM one-sentence tier rationale with template fallback | A | P1 | 10 | Rationale present for every ESCALATE/UNSUPPORTED finding; fallback works with the API off |
| [ ] | SF-018 | Source availability via target repo tree (cached 60 s) | A | P0 | 10 | `source_available` true for the 8 demo files once the target repo is pushed |
| [ ] | SF-019 | Findings API (list, filters, detail) + `/api/ingest` + `/api/ingest/seed` | A | P0 | 20 | Filters work; seed loads 200 findings; upload of CSV/SARIF/JSON works |
| [ ] | SF-020 | Baseline metrics endpoints (summary, backlog, funnel with run values at zero) | A | P0 | 15 | Summary shows 96 open, 39 critical+high, 42 older than 90 d, ≈653.9 h **[C6]** |

## Epic C — Target repo (Phase 2, Dev B) — commits go to `secureflow-demo-target`

| ✓ | ID | Ticket | Owner | Pri | Est | Acceptance criteria |
|---|---|---|---|---|---|---|
| [ ] | SF-030 | Repo scaffold: README, `requirements.txt`, `pytest.ini` (marker `exploit`), root `conftest.py` | B | P0 | 5 | `pytest --collect-only` works **[T1]** |
| [ ] | SF-031 | `notification-svc` File2.py SQL injection + tests | B | P0 | 5 | functional pass, exploit fail |
| [ ] | SF-032 | `data-pipeline` File4.py insecure deserialization + tests | B | P0 | 5 | same |
| [ ] | SF-033 | `analytics-engine` File16.py insecure TLS + tests | B | P0 | 5 | same **[T2]** |
| [ ] | SF-034 | `search-indexer` File43.py hardcoded secret (fake, non-provider pattern) + tests | B | P0 | 5 | same; push is not blocked by push protection |
| [ ] | SF-035 | `admin-dashboard` File47.py XSS + tests | B | P0 | 5 | same |
| [ ] | SF-036 | `data-pipeline` File20.py open redirect + tests | B | P0 | 5 | same **[T3]** |
| [ ] | SF-037 | `admin-dashboard` File36.py path traversal + tests | B | P0 | 5 | same |
| [ ] | SF-038 | `payment-api` File34.py SQL injection (LIKE) + tests | B | P0 | 5 | same |
| [ ] | SF-039 | Baseline verification and push: functional all pass, 8 exploit tests fail, bandit flags expected files | B | P0 | 5 | Output pasted in `Context.md`; repo public or shared with organizers **[T4]** |

## Epic D — Agent pipeline (Phase 3, Dev A)

| ✓ | ID | Ticket | Owner | Pri | Est | Acceptance criteria |
|---|---|---|---|---|---|---|
| [ ] | SF-040 | LLM wrapper: JSON mode, timeout, retry, token usage | A | P0 | 10 | Returns parsed dict + usage; bad JSON retried once |
| [ ] | SF-041 | GitHub tool: tree, file, zipball, branch, commit, draft PR, PR state | A | P0 | 20 | Can create and read a PR on the target repo in a test **[C7]** |
| [ ] | SF-042 | Sandbox: zipball extract to temp dir, safe subprocess runner, scrubbed env, timeout, path containment | A | P0 | 15 | Child env contains no keys; path traversal attempts rejected |
| [ ] | SF-043 | Patch policy gate (AST) | A | P0 | 15 | Unit tests: rejects `os.system`, new `subprocess`, disallowed import, multi-file change, oversized patch; accepts a clean fix **[C8]** |
| [ ] | SF-044 | Validator: baseline tests, apply patch, syntax, functional, exploit, bandit delta, junit parse | A | P0 | 30 | Known-good patch for File2 passes; known-bad fails with evidence |
| [ ] | SF-045 | Analyzer agent with drift handling | A | P0 | 20 | Reports "reported line X, found at line Y"; works when reported line is outside the file |
| [ ] | SF-046 | Fixer agent (full-file patch, explanation, confidence, risk, retry with error feedback) | A | P0 | 20 | Returns valid JSON; retry prompt includes validator failure **[C9]** |
| [ ] | SF-047 | PR agent: branch, commit, labels, draft PR body with evidence | A | P0 | 15 | Draft PR visible on GitHub with the template body |
| [ ] | SF-048 | LangGraph assembly: state, nodes, conditional retry edges, event emission | A | P0 | 20 | Graph runs end to end locally; retry loop observable in events |
| [ ] | SF-049 | Run lifecycle: remediate endpoint (202), background execution, events endpoint, guards | A | P0 | 20 | `POST /remediate` then polling shows live events; 409 on duplicate |
| [ ] | SF-050 | End-to-end test on VULN-0169 | A | P0 | 10 | Draft PR opened with passing evidence; commit **[C10]** |

## Epic E — Persistence, ops and deploy (Phase 5, Dev A)

| ✓ | ID | Ticket | Owner | Pri | Est | Acceptance criteria |
|---|---|---|---|---|---|---|
| [ ] | SF-060 | Firestore store implementation | A | P0 | 20 | Same contract tests pass; documents visible in console |
| [ ] | SF-061 | Batch remediation with concurrency and total-run caps | A | P1 | 15 | "top 3 criticals" starts 3 runs; 4th waits; cap returns 429 |
| [ ] | SF-062 | PR sync: merged/closed state, time-to-merge, finding status transitions | A | P0 | 15 | Merging a PR on GitHub changes status to MERGED after sync |
| [ ] | SF-063 | "Scan repo now": bandit on target zipball → SARIF → ingest | A | P1 | 20 | Returns real SARIF-derived findings with source `sarif` |
| [ ] | SF-064 | Full metrics: MTTR, acceptance (with n), hours saved, funnel, backlog timeline, token averages | A | P0 | 20 | Matches definitions in `TAD.md` §8.2 |
| [ ] | SF-065 | Backend Dockerfile, service account, `env.prod.yaml`, deploy to Cloud Run | A | P0 | 25 | Live URL; smoke tests pass **[C11]** |
| [ ] | SF-066 | Live smoke test: seed → remediate one finding on Cloud Run → PR opens | A | P0 | 10 | PR opened by the deployed service |

## Epic F — Frontend (Phases 4 and 6, Dev B)

| ✓ | ID | Ticket | Owner | Pri | Est | Acceptance criteria |
|---|---|---|---|---|---|---|
| [ ] | SF-070 | Design tokens: Tailwind config, `globals.css`, fonts, `.bg-space`, `.stars` | B | P0 | 10 | Matches `Design.md` §4 |
| [ ] | SF-071 | UI primitives: `ArrowOrb`, `PillButton`, `BracketLabel`, `GlassCard`, `Badge` family, `Skeleton`, `Toast`, `EmptyState` | B | P0 | 25 | Storybook-free demo page shows all variants |
| [ ] | SF-072 | Layout shell: `TopBar`, `FloatingNav`, `ScrollHint`, `Constellation` | B | P0 | 20 | Matches template anatomy **[C12]** |
| [ ] | SF-073 | Landing page: hero, how it works, by the numbers | B | P0 | 25 | Real numbers from API; rise animation; CTA works **[C13]** |
| [ ] | SF-074 | `lib/api.ts`, `lib/types.ts`, SWR hooks | B | P0 | 10 | Typed against `TAD.md` §8 |
| [ ] | SF-075 | Dashboard: 4 KPIs, backlog chart, age/severity chart, funnel, MTTR compare, recent runs | B | P0 | 45 | All numbers from API; empty states before first run **[C14]** |
| [ ] | SF-076 | Findings page: table, filters, drawer, Remediate, batch button, Import modal, Scan repo | B | P0 | 45 | Remediate starts a run and routes to run detail **[C15]** |
| [ ] | SF-077 | Run detail: agent graph, live trace, diff, evidence, PR tab, escalated card | B | P0 | 50 | Live updates every 2 s; retry arrow shown when it happens **[C16]** |
| [ ] | SF-078 | Runs list page | B | P1 | 10 | Table links to detail |
| [ ] | SF-079 | Loading, empty, error states and toasts across pages | B | P1 | 15 | No blank cards anywhere |
| [ ] | SF-080 | Frontend Dockerfile, env file, deploy `secureflow-web` | B | P0 | 20 | Live URL works through proxy; key not in browser bundle **[C17]** |

## Epic G — Rehearsal and submission (Phases 7 and 8)

| ✓ | ID | Ticket | Owner | Pri | Est | Acceptance criteria |
|---|---|---|---|---|---|---|
| [ ] | SF-090 | End-to-end rehearsal ×2 on the live deployment | Both | P0 | 20 | Full demo script from `PRD.md` §10 runs without edits |
| [ ] | SF-091 | Produce real PRs for the fix-ready findings; merge most, close one with a reviewer comment | Both | P0 | 15 | ≥ 6 real PRs, acceptance rate computed from real data |
| [ ] | SF-092 | README: problem, architecture, setup, deploy, honesty note on synthetic data | A | P0 | 10 | Short and accurate **[C18]** |
| [ ] | SF-093 | Architecture diagram exported (`docs/architecture.png`) from `TAD.md` §1 | B | P0 | 10 | Shows agents, tools, GCP services |
| [ ] | SF-094 | Slides (PDF or link) following the 7-minute split | B | P0 | 20 | Problem, solution, agents, demo, stack, scale |
| [ ] | SF-095 | Backup screen recording of a full run | Both | P0 | 10 | File saved locally |
| [ ] | SF-096 | Submission checklist: live links, repo link, slides, diagram, team and member names; final commit **[C19]** | Both | P0 | 10 | All items submitted before the deadline |

## Stretch (P2, only if ahead)

| ✓ | ID | Ticket | Owner | Est | Acceptance |
|---|---|---|---|---|---|
| [ ] | SF-100 | Dependency bump agent for Outdated Dependency (manifest edit + install check) | A | 40 | PR bumps a pinned version with reasoning |
| [ ] | SF-101 | JavaScript adapter (`node --check` + test run) | A | 45 | JS finding remediated with validation |
| [ ] | SF-102 | SSE streaming for the trace instead of polling | A+B | 25 | Trace updates without polling |
| [ ] | SF-103 | Vertex AI (Gemini) provider behind the LLM wrapper | A | 25 | Switch with `LLM_PROVIDER=vertex` |
| [ ] | SF-104 | Per-agent average duration chart on dashboard | B | 15 | Bars per agent |

---

## Dependency map (critical path)

SF-003 → SF-010..016 → SF-019/020 (unblocks dashboard)
SF-030..039 (target repo) → SF-018 → SF-044 → SF-050
SF-040, 041, 042, 043 → SF-044 → SF-045, 046 → SF-048 → SF-049 → SF-050
SF-060 → SF-065 → SF-066 → SF-080 → SF-090

## Definition of done (per ticket)

- Acceptance criteria met and tested (command or screenshot noted in `Context.md`).
- No secrets staged; `git status` reviewed.
- Code is simple enough that either teammate can explain it to the judges.
- Ticket marked `[x]` here, `Context.md` updated, work committed in its batch.
