# Household Financial Copilot

## AI-Powered Expense Tracking, Household Finance, and Analytics Platform

### Vision

Build an AI-powered household finance platform capable of ingesting screenshots, PDFs, and emails from multiple banks, automatically extracting transactions, assigning ownership, categorizing expenses, maintaining a review queue for uncertain transactions, and providing advanced analytics and forecasting.

---

# Instructions
1. It will be a project to showcase in my portfolio and to post on github, so efficiency, documentation and visuals are important.
2. Although it will be on my portfolio, I don't want to post anything that would show any of my personal financial data or information, so let's think about that on the design decisions.
2. Let's be time-efficient and not over-engineer.
3. Let's not spend any money (or not too much) on the project. Local or free is fine.



# Core Objectives

- Multi-bank support (Millennium, Santander, Revolut, N26, Wise, etc.)
- Email-based ingestion
- AI transaction extraction from screenshots and PDFs
- Household ownership tracking (Rafael, Heloisa, Shared)
- Human-in-the-loop review queue
- Analytics and forecasting
- AI copilot for natural language financial queries

---

# Architecture

Email / PDF / Screenshot
→ FastAPI Ingestion Layer
→ OpenAI Vision Extraction
→ Normalization
→ Ownership Assignment
→ Review Queue
→ DuckDB
→ Analytics + Forecasting + AI Copilot

---

# Technology Stack

## Backend
- Python
- FastAPI

## Database
- DuckDB

## Data Modeling
- dbt

## AI
- OpenAI Vision
- LangGraph (future)

## Frontend
- Streamlit

## Infrastructure
- Docker
- GitHub Actions
- Azure

---

# Household Model

Users:
- Rafael
- Heloisa
- Shared

Each transaction contains:
- Date
- Merchant
- Amount
- Category
- Owner
- Confidence Score
- Source File
- Bank

---

# Email Workflow

Send screenshots or PDFs to:

expenses@domain.com

Subject examples:

[Rafael]
[Heloisa]
[Shared]

Pipeline:

1. Receive email
2. Download attachment
3. Extract transactions with AI
4. Normalize merchants
5. Assign ownership
6. Store in DuckDB

---

# Review Queue

Purpose:

Only uncertain transactions require human validation.

Flow:

Transaction
→ AI Classification
→ Confidence Score

If confidence > 90%:
- Auto approve

Otherwise:
- Send to review queue

Review actions:
- Approve
- Edit
- Reject

---

# Categorization

Examples:

Income:
- Salary
- Bonus
- Investments

Expenses:
- Groceries
- Restaurants
- Transportation
- Utilities
- Shopping
- Entertainment
- Healthcare
- Travel
- Insurance

---

# Analytics

Household Dashboard:
- Income
- Expenses
- Savings Rate
- Cash Flow

Ownership Dashboard:
- Rafael Spending
- Heloisa Spending
- Shared Spending

Merchant Dashboard:
- Top Merchants
- Merchant Trends

Subscription Dashboard:
- Netflix
- Spotify
- Amazon Prime
- Gym Memberships

---

# Forecasting

Potential models:
- MLForecast
- LightGBM
- CatBoost

Forecasts:
- Monthly Spending
- Savings
- Cash Flow
- Future Balance

---

# AI Copilot

Example questions:

- How much did we spend on groceries this year?
- What are our recurring expenses?
- Which category increased the most versus last month?
- How much does the household cost to run?

---

# Portfolio Value

Demonstrates:

- Data Engineering
- Analytics Engineering
- AI Engineering
- Backend Development
- Cloud Deployment
- Forecasting
- Human-in-the-loop AI Systems

---

# Development Roadmap

## Phase 1
- Email ingestion
- Screenshot upload
- AI extraction
- DuckDB storage

## Phase 2
- Review queue
- Streamlit interface

## Phase 3
- Ownership assignment
- Categorization

## Phase 4
- Analytics dashboards

## Phase 5
- AI Copilot

## Phase 6
- Forecasting and anomaly detection
