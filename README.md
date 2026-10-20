# SecureFlow AI

> Built for hackathon **PS-09 — Security Vulnerability Auto-Remediation Pipeline**
> Finale: Tue 20 Oct 2026, NIC Islamabad · 4-hour on-site build

**SecureFlow AI** is an agentic DevSecOps pipeline that turns security-scanner findings into
validated, review-ready draft pull requests. A team of five LangGraph agents (Triage, Analyzer,
Fixer, Validator, PR) reads a finding, locates the vulnerable code, writes a minimal patch with
an explanation, proves the fix with exploit tests, and opens a **draft PR** on GitHub. A human
reviews and merges.

**One-line pitch:** "Scanners find vulnerabilities. SecureFlow fixes them, and proves it."

---

## Honesty note

The dataset (`backend/data/ps09_vulnerability_scans.csv`) is **synthetic**. The companion repo
`secureflow-demo-target` was built on the day of the hackathon to contain real vulnerable Python
files at 8 of the CSV paths. All patches are generated live by the LLM — no hardcoded outputs,
no pre-recorded results presented as live.

---

## Agent architecture

```
Triage -> Analyzer -> Fixer -> Validator --(pass)--> PR Agent
                       ^--(fail, <2 retries)---------/
```

| Agent | Role |
|---|---|
| Triage | Tiers finding: AUTO_FIX / DEPENDENCY / ESCALATE / UNSUPPORTED_LANG |
| Analyzer | Fetches file from GitHub, locates vulnerable code (handles line drift) |
| Fixer | LLM generates minimal full-file patch + explanation + confidence + risk |
| Validator | Policy gate, baseline tests, apply patch, syntax, functional, exploit, bandit |
| PR Agent | Creates branch, commits patch, opens draft PR with evidence table |

---

## Tech stack and GCP services

| Layer | Choice |
|---|---|
| Agent framework | LangGraph (Python 3.12) |
| LLM | OpenAI (provided key) |
| Backend | FastAPI + Uvicorn on Cloud Run (secureflow-api) |
| Database | Firestore (Native mode, asia-south1) |
| GitHub integration | PyGithub + fine-grained PAT |
| Validation sandbox | ast, py_compile, pytest, bandit in temp dir |
| Frontend | Next.js 14 App Router + Tailwind + Recharts + SWR on Cloud Run (secureflow-web) |
| Build | Cloud Build + Artifact Registry via gcloud run deploy --source . |

---

## How to run locally

### Backend

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
rem Edit .env: set API_KEY, OPENAI_API_KEY, OPENAI_MODEL_FAST, OPENAI_MODEL_CODE, GITHUB_TOKEN, GITHUB_OWNER
uvicorn app.main:app --reload --port 8080
```

Seed the dataset and run tests:

```cmd
curl -X POST -H "X-API-Key: change-me" http://localhost:8080/api/ingest/seed
pytest -q
```

### Frontend

```cmd
cd frontend
copy .env.local.example .env.local
rem Edit .env.local: BACKEND_URL=http://localhost:8080, BACKEND_API_KEY=change-me
npm install
npm run dev
```

---

## How to deploy (GCP, Windows cmd)

### One-time setup

```cmd
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
set GCP_PROJECT_ID=YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com firestore.googleapis.com
gcloud firestore databases create --location=asia-south1
gcloud iam service-accounts create secureflow-runner --display-name="SecureFlow runtime"
gcloud projects add-iam-policy-binding %GCP_PROJECT_ID% ^
  --member="serviceAccount:secureflow-runner@%GCP_PROJECT_ID%.iam.gserviceaccount.com" ^
  --role="roles/datastore.user"
```

### Backend deploy

Copy `env.prod.example.yaml` to `env.prod.yaml`, fill in real values, then:

```cmd
cd backend
gcloud run deploy secureflow-api ^
  --source . ^
  --region asia-south1 ^
  --allow-unauthenticated ^
  --service-account secureflow-runner@%GCP_PROJECT_ID%.iam.gserviceaccount.com ^
  --env-vars-file ..\env.prod.yaml ^
  --no-cpu-throttling ^
  --min-instances 1 ^
  --max-instances 2 ^
  --memory 1Gi ^
  --cpu 1 ^
  --timeout 900
```

### Frontend deploy

Copy `env.web.example.yaml` to `env.web.yaml`, fill in `BACKEND_URL` and `BACKEND_API_KEY`, then:

```cmd
cd frontend
gcloud run deploy secureflow-web ^
  --source . ^
  --region asia-south1 ^
  --allow-unauthenticated ^
  --env-vars-file ..\env.web.yaml ^
  --min-instances 1 ^
  --memory 512Mi
```

---

## Team

- **Dev A** - Backend and agents
- **Dev B** - Frontend and target repo
