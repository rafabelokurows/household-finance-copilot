# Household Finance Copilot

An AI-powered household finance platform for Rafael and Heloisa. Ingests bank statements via Gmail or manual upload, extracts transactions using Google Gemini Flash, and provides a full review + analytics suite.

## Why this exists

Most personal finance tools assume you live in one country, bank with one institution, and want your data sent to a third-party cloud. That doesn't work well for a household that spans multiple Portuguese banks, has joint and individual expenses, and values keeping financial data off external servers.

This app exists to answer one simple question: *where is our money going?* Bank statements arrive as PDFs or images across several email accounts. Logging into each bank's portal to piece together a monthly picture is tedious and error-prone. This tool automates the ingestion — polling email attachments, running vision AI over the documents, and landing everything in a single review queue where transactions can be confirmed, corrected, and categorised before hitting the database.

The review step is intentional. AI extraction isn't perfect, especially across different bank layouts and receipt formats. Rather than silently accepting every parsed transaction, the app surfaces low-confidence extractions for human review. High-confidence ones are approved automatically; the rest wait in the queue. Nothing enters the analytics until someone has signed off on it.

## Who it's for

Built for two people: **Rafael** and **Heloisa**. Transactions are tagged per person or as shared, so monthly spend can be broken down individually or as a household. It's a private, self-hosted tool — not a product, not a SaaS, not designed to scale beyond a single home.

## Features

- **Multi-bank ingestion**: Accepts screenshots and PDFs from Portuguese banks (e.g. Millennium BCP, Caixa Geral, Santander PT) — designed to work across different countries' statement layouts
- **AI extraction with Gemini Flash**: Uses Google Gemini 2.0 Flash vision to parse transactions from images and PDFs — free tier friendly
- **Review queue**: Every extracted transaction goes through a confidence-gated review queue before being committed to the database
- **Source document viewer**: Each transaction in the review queue can display its original receipt or bank statement — view inline or download
- **Analytics dashboard**: Monthly spend by category, trends, and per-user breakdowns
- **Authentication**: Login/logout with session token management

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python + FastAPI (port 8000) |
| Frontend | React 19 + Vite (port 5173) |
| Database | PostgreSQL via Supabase |
| AI / Vision | Groq — Llama 3.3 70B (text) + Llama 3.2 11B Vision (images) |
| Email ingestion | Gmail API (`google-api-python-client`) |
| Deployment | Vercel (frontend) + Render (backend) + Supabase (DB) |

## Quick Start (local)

```bash
# 1. Clone the repo
git clone <repo-url>
cd Household-Finance-Copilot

# 2. Configure backend environment
cp backend/.env.example backend/.env
# Edit backend/.env — set GROQ_API_KEY and DATABASE_URL (Supabase connection string)

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Start the backend
uvicorn backend.main:app --reload --port 8000

# 5. Install frontend dependencies
cd frontend-react && npm install

# 6. Configure frontend environment
echo "VITE_API_BASE=http://localhost:8000" > .env

# 7. Start the frontend
npm run dev

# Frontend: http://localhost:5173
# Backend API docs: http://localhost:8000/docs
```

Test credentials (local dev only):
- `rafael` / `rafael123`
- `heloisa` / `heloisa123`

> **Without `GROQ_API_KEY`**: app runs in test mode — uploads and Gmail attachments are accepted but no transactions are extracted.

## Gmail Setup

Ingesting emails requires Google Cloud credentials:

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `credentials.json` and place it in the project root
5. On first run, the backend opens a browser for OAuth consent — a `token.json` is saved locally for subsequent runs
6. The poller runs every 5 minutes by default, fetching emails with PDF/image attachments

Relevant `.env` vars (all optional — defaults work out of the box):

```
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
GMAIL_POLL_INTERVAL=300
```

Both `credentials.json` and `token.json` are gitignored and must never be committed.

> **Multiple email accounts**: set up forwarding from all statement-receiving accounts to one dedicated Gmail and point the poller at that account.

## Privacy

No real financial data is stored in this repository. The `data/` directory is gitignored.

## Architecture

```
  Browser → Vercel CDN (React SPA, port 5173 local)
                  ↓ HTTPS API calls
          Render / localhost (FastAPI, port 8000)
                  |
                  ├── Groq API (Llama 3 — text + vision extraction)
                  ├── Gmail API (background poller thread)
                  └── Supabase (PostgreSQL)
                            ├── transactions
                            ├── documents (BLOB)
                            ├── tags / transaction_tags
                            ├── category_rules
                            └── gmail_poll_state
```

## Architecture Decisions

Key decisions (AI model, database, email strategy, deployment, privacy) are documented in [docs/ADR.md](docs/ADR.md).

## Users

- **Rafael**
- **Heloisa**
- **Shared** — joint expenses tracked separately
