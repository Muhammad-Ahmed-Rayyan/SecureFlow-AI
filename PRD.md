# PRD.md — SecureFlow AI

> Product Requirements Document · Hackathon PS-09 · Finale: Tue 20 Oct 2026, NIC Islamabad
> Read this first, then `TAD.md`. Tickets live in `FTL.md`, phases in `Phase.md`, live state in `Context.md`.

---

## 1. Summary

**SecureFlow AI** is an agentic DevSecOps pipeline that turns security-scanner findings into **validated, review-ready draft pull requests**.

A team of five LangGraph agents (Triage, Analyzer, Fixer, Validator, PR) reads a finding, locates the vulnerable code, writes a minimal patch with an explanation, proves the fix with exploit tests, and opens a **draft PR** on GitHub. A human reviews and merges. A live dashboard tracks MTTR, auto-fix acceptance rate and backlog trend.

One-line pitch: **"Scanners find vulnerabilities. SecureFlow fixes them, and proves it."**

---

## 2. Problem

Enterprise scanners (Fortify, SonarQube, Snyk, Dependabot, Trivy, Mend) are excellent at detection, but fixing is manual. A developer spends 4–10 hours per vulnerability reading the advisory, researching the fix, patching, testing and raising a PR. Hundreds of findings per quarter consume 20–30% of engineering capacity and security debt keeps growing.

### What our dataset shows (`ps09_vulnerability_scans.csv`, 200 records)

| Fact | Value |
|---|---|
| Findings still open or in progress | **96** (48%) |
| Critical + High in that backlog | **39** (12 critical) |
| Backlog older than 90 days | **42** |
| Baseline manual fix effort (mean, n=146 non-null) | **6.82 h** |
| Estimated backlog effort (missing times filled with per-severity median) | **≈ 654 engineer-hours ≈ 16 engineer-weeks** |
| Findings that stayed open before being fixed (Fixed + Verified, mean) | **≈ 90 days** |
| Findings with no scanner-suggested fix | **58%** (52% inside the backlog) |

Illustrative cost: at an assumed loaded cost of $60/h (assumption, not data) the open backlog is about $39k of pure fix effort.

---

## 3. Users

| Persona | Job | What they need from SecureFlow |
|---|---|---|
| **AppSec engineer** | Owns the backlog, decides what gets fixed first | Triage that ranks by risk, explains why a finding was or was not auto-fixed, shows clean data |
| **Developer (reviewer)** | Reviews the fix before merge | A small diff, plain-English root cause, proof the exploit no longer works, confidence and risk rating |
| **Engineering manager** | Funds and tracks security work | MTTR reduction, acceptance rate, backlog trend, hours saved |

---

## 4. Goals and success metrics

These match the judges' evaluation criteria: **fix acceptance rate, MTTR reduction, code quality of patches**.

| Goal | Metric | Target for the live demo (targets, not claims) |
|---|---|---|
| Fixes get accepted | Acceptance rate = merged / (merged + closed unmerged), shown with sample size n | ≥ 75% of decided PRs |
| Fixes are fast | Time from "Remediate" click to review-ready draft PR | median < 5 min (baseline 6.82 h effort) |
| Fixes are correct | Validation pass (policy gate, syntax, functional tests, exploit tests, bandit delta) within 2 attempts | ≥ 75% of runs |
| Fixes are explainable | Every PR carries root cause, diff explanation, before/after evidence, confidence, risk | 100% of PRs |
| Backlog shrinks | Live backlog count drops as PRs open and merge | visible during demo |

Rules for honest metrics:
- MTTR is reported as **time-to-review-ready-PR** and, separately, **time-to-merge** (measured from GitHub). Agent time is never presented as total fix time, because human review is still required.
- Acceptance rate comes only from **real PRs** on the target repo. Nothing is pre-seeded.

---

## 5. Scope

### In scope (MVP built today)

- Ingest scan results in **CSV, SARIF and JSON** into one normalized schema, with data-quality flags.
- **Triage Agent**: tiers every finding (auto-fix / dependency / escalate / unsupported language), ranks by priority, writes a rationale.
- **Analyzer, Fixer, Validator, PR agents** in a LangGraph with a validation retry loop (max 2 retries).
- **Python** is fully supported end to end. JS, TS and Java are ingested, triaged and shown on the dashboard as "adapter not enabled".
- **Proof of fix**: exploit tests that fail before the patch and pass after, plus bandit re-scan where applicable.
- **Draft PR** creation on `secureflow-demo-target` with full explanation. Never auto-merge.
- **Dashboard** (MTTR, acceptance rate, backlog, remediation funnel), **findings table**, **run detail** with live agent trace.
- **"Scan repo now"**: runs bandit on the target repo, produces real SARIF, ingests it through the same pipeline.
- Deployed on **GCP** (Cloud Run for API and web, Firestore, Cloud Build, Artifact Registry).

### Out of scope (roadmap, stated honestly in the pitch)

- JS / TS / Java remediation adapters.
- Outdated-dependency bump agent (stretch ticket only).
- Auto-merge, multi-tenant auth, GitHub App webhooks, Pub/Sub queueing.
- Fixing issues that need architectural change (CSRF) or that are likely scanner false positives (Buffer Overflow in managed languages): these are **escalated to a human** with a reason.

---

## 6. Functional requirements

Each FR maps to tickets in `FTL.md`.

| ID | Requirement | Tickets |
|---|---|---|
| FR-1 | Import CSV, SARIF, JSON; normalize to one `Finding` schema | SF-010..014 |
| FR-2 | Flag data-quality problems (language mismatch, description mismatch, duplicates, missing fix time) | SF-015 |
| FR-3 | Tier each finding and compute a priority score; explain the decision | SF-016, 017 |
| FR-4 | Know which findings have source code available in the connected repo | SF-018 |
| FR-5 | Analyzer locates the vulnerable code even when the reported line has drifted | SF-045 |
| FR-6 | Fixer returns a minimal full-file patch with explanation, confidence, risk | SF-046 |
| FR-7 | Patch policy gate rejects unsafe patches before any execution | SF-043 |
| FR-8 | Validator runs syntax, functional tests, exploit tests (before and after) and bandit delta in an isolated temp dir | SF-042, 044 |
| FR-9 | Failed validation feeds errors back to the Fixer, max 2 retries, then marks the run FAILED with logs | SF-048 |
| FR-10 | PR agent opens a **draft** PR with branch, commit, labels and an evidence-rich body | SF-047 |
| FR-11 | Live run trace: every agent step is visible in the UI within 2 seconds | SF-049, 077 |
| FR-12 | Batch remediation ("top 3 criticals") with concurrency and budget caps | SF-061 |
| FR-13 | PR state sync (merged / closed) drives acceptance rate and time-to-merge | SF-062 |
| FR-14 | Dashboard shows MTTR, acceptance, backlog, funnel, hours saved | SF-064, 075 |
| FR-15 | "Scan repo now" produces real SARIF and ingests it | SF-063 |

### Non-functional requirements

- **Latency:** one remediation completes in under ~3 minutes typical.
- **Explainability:** every line of code must be explainable by the team. Keep modules small, plain and commented.
- **Safety:** draft PRs only; sandboxed validation; scrubbed environment; secrets only in environment variables (see `Security.md`).
- **Cost control:** max concurrent runs, max total runs, token usage tracked per run.
- **Reliability:** Cloud Run with `--min-instances 1 --no-cpu-throttling` so background runs are not throttled.

---

## 7. Dataset handling and assumptions

The CSV is synthetic and internally inconsistent. We treat that as a product feature (data-quality triage), not something to hide.

| Observation | Handling |
|---|---|
| `language` matches the file extension in only 39 of 200 rows (161 mismatches) | Trust the **file extension**; flag `LANG_MISMATCH` |
| Descriptions are placeholders and often contradict `vulnerability_type` | Never trust description; decide from type plus real code; flag `DESC_MISMATCH` |
| File paths are placeholders (`src/main/service/File2.py`); line numbers up to 499 | We built `secureflow-demo-target` with real vulnerable files at 8 of the CSV paths. Line numbers are **hints**; the Analyzer handles line drift |
| `fix_time_hours` missing on 54 rows | Impute per-severity median for backlog estimates; flag `MISSING_FIX_TIME`; baseline mean uses non-null rows only |
| CVE `CVE-2026-91204` appears on two unrelated findings | Flag `DUP_CVE` |
| 18 file paths repeat across findings | Flag `DUP_FILE`; remediate one finding per run |
| No detection or resolution dates, only `days_open` | Backlog is shown by age bucket and severity from the CSV, plus a **live** line from real runs. Assumption stated in README |

**Honesty rule for the demo (disqualification rule 6):** tell the judges the dataset is synthetic and that we built a target repo whose files match 8 of the CSV records. Every patch is generated live by the LLM. No hardcoded outputs, no pre-recorded results presented as live.

---

## 8. Agentic design summary

| Agent | Autonomy | Tools | Output |
|---|---|---|---|
| **Triage** | Decides tier, priority, whether to proceed or escalate | rules + LLM rationale, repo tree lookup | tier, reason, priority, source availability |
| **Analyzer** | Decides where the bug is and why | GitHub file fetch, AST/line search | location (with drift), root cause, CWE, fix strategy |
| **Fixer** | Decides how to patch | LLM code generation | full patched file, explanation, confidence, risk |
| **Validator** | Decides pass or fail, drives retry | sandbox, pytest, bandit, AST policy gate | structured before/after evidence |
| **PR** | Decides PR content | GitHub API | branch, commit, draft PR with evidence |

Autonomy boundary: agents plan, use tools and take actions up to **opening a draft PR**. A human always makes the merge decision.

---

## 9. Hackathon compliance matrix

| Requirement | How we meet it |
|---|---|
| 1. Problem statement PS-09 | Built exactly for it, using the provided CSV |
| 2. Agentic AI | 5 agents with planning, tools, actions, retry loop |
| 3. Deployment on GCP + Antigravity | Cloud Run (API + web), Firestore, Cloud Build, Artifact Registry; built in Antigravity |
| 4. Scalability | Section 13 roadmap and `TAD.md` §15 |
| 5. Working demo | Live remediation of real findings; backup screen recording made on the day |

Disqualification avoidance: no code before reveal; no copied projects; commit in logical batches throughout the day; keys only in env vars; team can explain every file; no faked outputs.

---

## 10. Demo script (3 minutes of the 7)

1. **Dashboard (30 s):** 96 open findings, ≈654 engineer-hours of debt, 52% of backlog with no scanner fix.
2. **Remediate a CRITICAL SQL injection (75 s):** click once; the trace shows Triage, Analyzer (finds the bug at a drifted line), Fixer, Validator (one failure, one retry, then pass), PR agent.
3. **Open the draft PR (30 s):** diff, root cause, exploit tests failing before and passing after.
4. **Merge it (15 s):** dashboard backlog drops, acceptance rate updates, time-to-merge appears.
5. **Escalation (15 s):** a Buffer Overflow finding in a Python file that Triage refused to patch, with its reasoning.
6. **Batch (15 s, if time):** "Remediate top 3 criticals" running in parallel.

Backup: a screen recording of a full successful run made during Phase 8.

---

## 11. Judging criteria mapping

| Criterion | Our answer |
|---|---|
| Innovation | Proof-of-fix via exploit tests; triage that says no; real SARIF round trip; drift-tolerant analysis |
| Functionality | Full live loop: finding → patch → validation → draft PR → merge → metrics |
| Scalability | Stateless Cloud Run workers, Firestore, queue-ready design, language adapter interface |
| Real-world impact | Backed by dataset numbers (96 open, ≈654 h) and measured PR times |
| Technical execution | LangGraph with conditional retry edges, sandboxed validation, policy gate, GCP deployment |

---

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| LLM writes a bad patch | Policy gate, exploit tests, retry loop, draft PR, human review |
| OpenAI credits or rate limits | Run caps, small models for triage, token tracking |
| Cloud Run throttles background work | `--no-cpu-throttling`, `--min-instances 1` |
| Internet or API failure at demo | Backup recording; rehearse twice; keep 2 findings pre-validated locally (still run live) |
| GitHub push protection blocks fake secrets | Use obviously fake values that do not match real provider patterns |
| Running out of time | Strict phase budget in `Phase.md`; P2 tickets are optional |

---

## 13. Roadmap to market

| Stage | What it adds |
|---|---|
| **Hackathon MVP (today)** | Python remediation, 5 agents, dashboard, Cloud Run |
| **Scalable MVP** | Pub/Sub or Cloud Tasks queue, GitHub App with webhooks, JS/TS/Java adapters, multi-repo, per-tenant Firestore, Secret Manager, Vertex AI option |
| **Market-ready product** | Native scanner connectors (Snyk, SonarQube, Fortify, Dependabot), policy engine (auto-approve rules by severity), audit trail and SOC2 posture, SSO, fix-quality learning loop from accepted and rejected PRs |

Pricing idea: per-repository subscription with a usage component per merged fix. ROI formula: hours saved × loaded engineer cost.

---

## 14. Non-goals

No auto-merge. No claim of fixing every vulnerability class. No real customer data. No production-grade multi-tenancy today.

---

## 15. Glossary

- **Tier:** triage decision (AUTO_FIX, DEPENDENCY, ESCALATE, UNSUPPORTED_LANG).
- **Fix-ready:** a finding whose source file exists in the connected target repo and whose language adapter is enabled.
- **Exploit test:** a pytest test that demonstrates the vulnerability; must fail before the patch and pass after.
- **Drift:** the reported line number no longer matches where the bug actually is.
- **Policy gate:** static AST check that rejects unsafe or out-of-scope patches before execution.
