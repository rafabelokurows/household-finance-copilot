# Household Finance Copilot

An AI-powered household finance platform for Rafael and Heloisa. Ingests bank statements via Gmail or manual upload, extracts transactions using Google Gemini Flash, and provides a full review + analytics suite.

## Features

- **Multi-bank ingestion**: Accepts screenshots and PDFs from any Brazilian bank (Nubank, Itau, Bradesco, etc.)
- **AI extraction with Gemini Flash**: Uses Google Gemini 2.0 Flash vision to parse transactions from images and PDFs — free tier friendly
- **Review queue**: Every extracted transaction goes through a confidence-gated review queue before being committed to the database
- **Analytics dashboard**: Monthly spend by category, trends, forecasts (statsforecast), and per-user breakdowns
- **AI copilot**: Ask natural language questions about your finances — powered by Gemini
- **dbt data modeling**: Clean staging and mart layers on top of DuckDB for reliable reporting

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python + FastAPI (port 8000) |
| Frontend | Streamlit (port 8501) |
| Database | DuckDB (`data/finance.duckdb`) |
| AI / Vision | Google Gemini 2.0 Flash (`google-generativeai`) |
| Email ingestion | Gmail API (`google-api-python-client`) |
| Data modeling | dbt-duckdb |
| Deployment | Docker Compose (local only) |

## Quick Start

```bash
# 1. Clone the repo
git clone <repo-url>
cd Household-Finance-Copilot

# 2. Configure environment
cp .env.example .env
# Edit .env and fill in your GEMINI_API_KEY and other values

# 3. Start services
docker-compose up --build

# 4. Run dbt models (in a separate terminal)
cd dbt
dbt seed && dbt run

# 5. Open the app
# Frontend: http://localhost:8501
# Backend API docs: http://localhost:8000/docs
```

## Gmail Setup

Ingesting emails requires Google Cloud credentials:

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `credentials.json` and place it in the project root
5. Set `GMAIL_CREDENTIALS_PATH=credentials.json` in your `.env`
6. On first run, authenticate via the browser prompt — a `token.json` will be saved locally

Both `credentials.json` and `token.json` are gitignored and must never be committed.

## Privacy

No real financial data is stored in this repository. The `data/` directory is gitignored.

Use `dbt seed` with anonymized CSV files in `dbt/seeds/` to populate demo data for development.

## Architecture

```
                        +------------------+
                        |   Gmail API      |
                        |  (email poller)  |
                        +--------+---------+
                                 |
              Manual upload      |
                    |            v
                    |   +--------+---------+
                    +-->|  FastAPI Backend  |
                        |   (port 8000)    |
                        |                  |
                        |  Gemini Flash    |
                        |  (vision OCR)    |
                        +--------+---------+
                                 |
                        +--------v---------+
                        |    DuckDB        |
                        | data/finance.db  |
                        +--------+---------+
                                 |
                        +--------v---------+
                        |   dbt models     |
                        | staging / marts  |
                        +--------+---------+
                                 |
                        +--------v---------+
                        | Streamlit Frontend|
                        |   (port 8501)    |
                        | - Review queue   |
                        | - Analytics      |
                        | - AI copilot     |
                        +------------------+
```

## Users

- **Rafael** (`rafael.belokurows@primetag.net`)
- **Heloisa**
- **Shared** — joint expenses tracked separately
