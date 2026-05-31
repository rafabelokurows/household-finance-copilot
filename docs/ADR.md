# Architecture Decision Records

Captures the key decisions made during the design and build of Household Finance Copilot, including the options considered and the reasons for each choice.

---

## ADR-001 — AI Vision Model: Google Gemini Flash

**Status:** Accepted  
**Date:** 2026-05-31

### Context

The system needs to extract structured transaction data from unstructured inputs: bank statement screenshots (PNG/JPG) and PDF exports. This requires a multimodal model capable of reading financial documents and returning structured JSON.

### Options considered

| Option | Cost | Quality | Privacy |
|--------|------|---------|---------|
| OpenAI GPT-4o | ~$0.01–0.05/image | Best | Data sent to OpenAI |
| Google Gemini 2.0 Flash | Free (1M tokens/day) | Good | Data sent to Google |
| Ollama + LLaVA (local) | Free | Lower on dense docs | Data stays local |
| Claude Haiku | ~$0.003/image | Good | Data sent to Anthropic |

### Decision

**Google Gemini 2.0 Flash** via the `google-generativeai` SDK.

### Reasons

- Free tier covers 1 million tokens/day — far beyond personal household use
- Vision quality on financial documents is sufficient for the confidence-gated review queue to catch errors
- No ongoing cost for a personal portfolio project
- Native support for inline base64 image and PDF data without a separate file upload step

### Trade-offs

- Data leaves the machine (sent to Google). Acceptable for a household project; not suitable for a commercial or compliance-sensitive context.
- Gemini is not as accurate as GPT-4o on dense, multi-column bank statements. Mitigated by the confidence threshold and review queue (ADR-005).

---

## ADR-002 — Database: DuckDB

**Status:** Accepted  
**Date:** 2026-05-31

### Context

Need a database to store transactions, support analytical queries (aggregations by month, owner, category), and integrate cleanly with dbt and Python.

### Options considered

| Option | Requires server | Analytics | dbt support | File-based |
|--------|----------------|-----------|-------------|------------|
| PostgreSQL | Yes | Good | Yes | No |
| SQLite | No | Limited | Partial | Yes |
| DuckDB | No | Excellent (columnar) | Yes (dbt-duckdb) | Yes |
| Supabase | Cloud | Good | Yes | No |

### Decision

**DuckDB** — embedded columnar database stored as a single file (`data/finance.duckdb`).

### Reasons

- No server process to manage — runs in-process with Python
- Columnar storage makes analytical aggregations (GROUP BY month, owner, category) very fast
- Native `dbt-duckdb` adapter with zero configuration overhead
- Single-file database maps cleanly to a Docker volume mount
- Excellent Python integration via the `duckdb` package

### Trade-offs

- Only one writer at a time (single connection). Acceptable because this is a single-user app running as one Docker service. The singleton connection pattern in `db/client.py` enforces this.
- Not suitable if the app ever needs concurrent writes from multiple processes.

---

## ADR-003 — Email Ingestion: Gmail API OAuth Polling

**Status:** Accepted  
**Date:** 2026-05-31

### Context

The main data input flow is forwarding bank statement screenshots/PDFs by email. The system needs to receive those emails, extract attachments, and feed them into the extraction pipeline automatically.

### Options considered

| Option | Cost | Setup | Portfolio value |
|--------|------|-------|----------------|
| Gmail API (OAuth polling) | Free | Medium (Google Cloud project) | High |
| IMAP watcher | Free | Low | Medium |
| Mailgun / Postmark webhook | Paid | Medium | Medium |
| Manual upload only (skip email) | Free | Minimal | Low |

### Decision

**Gmail API** with OAuth 2.0, polling every 5 minutes via a daemon background thread.

### Reasons

- Free at personal usage scale
- OAuth 2.0 credential flow is a well-known portfolio skill
- Subject line convention (`[Rafael]`, `[Heloisa]`, `[Shared]`) is simple and requires no extra configuration per email

### Implementation details

- `credentials.json` — downloaded from Google Cloud Console, gitignored
- `token.json` — written after first OAuth browser prompt, gitignored, auto-refreshes
- Thread is a daemon so it exits cleanly when the main process exits
- If `credentials.json` is absent, polling is silently disabled — manual upload still works

### Trade-offs

- Requires a one-time interactive browser auth step (run locally before Docker)
- Gmail API has a quota of 1 billion units/day — polling at 5-minute intervals costs ~288 list calls/day, well within limits

---

## ADR-004 — Deployment: Local Docker Compose

**Status:** Accepted  
**Date:** 2026-05-31

### Context

The project needs to run somewhere. Options range from local-only to full cloud deployment.

### Options considered

| Option | Cost | Complexity | Live demo URL |
|--------|------|------------|---------------|
| Azure Container Apps | ~$10–30/month | High | Yes |
| Railway / Render free tier | Free | Low | Yes (with sleep) |
| Local Docker Compose | Free | Low | No |

### Decision

**Local Docker Compose** only, for now.

### Reasons

- Zero cost, forever
- Docker Compose file in the repo demonstrates infrastructure-as-code skills without cloud complexity
- The portfolio value is in the code, not in having a live URL
- Cloud deploy can be added later by extending `docker-compose.yml` with a cloud target

### Architecture

Two services:
- `backend` — FastAPI on `:8000`, build context is repo root, `./backend` volume-mounted for hot reload
- `frontend` — Streamlit on `:8501`, build context is `./frontend`, communicates with backend via `BACKEND_URL=http://backend:8000`

---

## ADR-005 — Confidence Threshold: 0.90

**Status:** Accepted  
**Date:** 2026-05-31

### Context

Gemini returns a per-transaction confidence score (0.0–1.0). The system needs a rule to decide which transactions are auto-approved vs sent to the human review queue.

### Decision

Transactions with `confidence >= 0.90` are auto-approved. Below 0.90, status is set to `pending` and the transaction enters the review queue.

The threshold is configurable via the `CONFIDENCE_THRESHOLD` environment variable.

### Reasons

- 0.90 is strict enough that only clearly legible, unambiguous transactions are auto-approved
- Low-confidence transactions (blurry screenshots, unusual formats, missing dates) surface to the review queue where a human can correct them
- Making it an env var means it can be tightened (e.g., 0.95) or loosened without a code change

### Trade-offs

- A higher threshold means more manual review; lower means more automation but more potential errors in the database. 0.90 is the starting point — tune based on real extraction quality.

---

## ADR-006 — Owner Assignment: Email Subject Convention

**Status:** Accepted  
**Date:** 2026-05-31

### Context

Each transaction must be assigned to an owner (Rafael, Heloisa, or Shared) to support per-person spending analytics. The system needs a way to know who a statement belongs to at ingestion time.

### Decision

- **Email path**: parse `[Rafael]`, `[Heloisa]`, or `[Shared]` from the email Subject header using a regex. Case-insensitive.
- **Upload path**: optional `owner` form field in `POST /upload`. If omitted, owner is `null` and can be assigned later via `PATCH /transactions/{id}`.

### Reasons

- Requires zero UI interaction for the email flow — just include the tag in the subject when forwarding
- Regex is simple and reliable; the pattern `\[(Rafael|Heloisa|Shared)\]` is unambiguous
- Untagged emails still work — transactions land as unowned and can be bulk-assigned in the review queue

### Trade-offs

- Convention must be remembered when forwarding emails. Could be forgotten. Mitigation: the review queue makes it easy to spot and fix unowned transactions.

---

## ADR-007 — Privacy: Gitignore Data + dbt Seed Demo Data

**Status:** Accepted  
**Date:** 2026-05-31

### Context

This is a public portfolio project. Real financial data must never appear in the git repository.

### Decision

Two-layer approach:

1. **Gitignore everything sensitive**: `data/`, `*.duckdb`, `.env`, `credentials.json`, `token.json`, `*.pdf`, `*.png`, `*.jpg`, `*.jpeg`, `attachments/`
2. **Demo data via dbt seeds**: `dbt/seeds/sample_transactions.csv` contains ~200 rows of entirely fake transactions (fake merchants, amounts, dates) that can be seeded with `dbt seed` to demonstrate the full analytics stack

### Reasons

- Hard gitignore boundary ensures no accidental commit of real data
- Fake seed data lets reviewers and interviewers run the full app and see real charts without any personal information
- README explicitly states the privacy approach

### Trade-offs

- Screenshots in the README must also use seed data (no real statements). This is enforced by convention, not tooling.

---

## ADR-008 — DuckDB Connection: Singleton Pattern

**Status:** Accepted  
**Date:** 2026-05-31

### Context

DuckDB supports only one writer per file at a time. FastAPI runs sync route handlers in a thread pool. Need a strategy for safe DB access across concurrent requests.

### Decision

Module-level singleton connection in `backend/db/client.py`. `get_connection()` creates the connection on first call and returns the same object on every subsequent call. Schema is initialized once at connection time.

### Reasons

- DuckDB's single-writer constraint means pooling would require serialization anyway
- FastAPI's `anyio` thread pool runs sync handlers concurrently, but DuckDB's GIL-based Python binding serializes execution at the C level — safe for reads and low-write-volume apps
- Simpler than a connection pool; no dependencies on SQLAlchemy or similar

### Trade-offs

- Not safe if the app is ever run with multiple worker processes (`uvicorn --workers 4`). The Docker Compose command uses a single worker, which is consistent with this design.

---

## ADR-009 — Gemini Input: Inline Base64 vs File Upload API

**Status:** Accepted  
**Date:** 2026-05-31

### Context

Gemini can receive file data in two ways: inline base64-encoded bytes in the request body, or via the File API (upload first, then reference by URI).

### Decision

**Inline base64** encoding via `inline_data` in the request part.

### Reasons

- Simpler: one API call instead of two
- No file lifecycle management (upload, get URI, delete after use)
- Bank statements are typically small (screenshots < 2MB, PDFs < 5MB) — well within Gemini's inline data limit of ~20MB

### Trade-offs

- If users ever try to ingest large multi-page PDF exports (>20MB), inline encoding will fail. The File Upload API would be needed. For now this is out of scope.
