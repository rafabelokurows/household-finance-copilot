# Phase 2 Frontend Design: Streamlit App

**Date:** 2026-06-03  
**Project:** Household Finance Copilot  
**Scope:** Review queue + Browse/Analytics + Secure login  
**Architecture:** Component-based Streamlit app with FastAPI backend integration

---

## 1. Overview

Phase 2 builds a Streamlit frontend for human-in-the-loop transaction review and analytics. The app connects to the existing FastAPI backend (port 8000) and DuckDB database.

**Data model:** Transactions are receipt-level or bank statement row-level (not itemized by product). A single receipt or bank transaction = one database entry with amount, merchant, category, and date.

**Core features:**
- Secure login (username/password with bcrypt hashing)
- Review Queue — validate extracted transactions from email ingestion (Gmail-sourced bank statements and receipts)
- Browse/Analytics — view processed transactions and spending insights

**Out of scope for Phase 2:**
- Manual receipt upload (deferred to Phase 3)
- Multi-user account management (admin panel)

---

## 2. Architecture

### 2.1 Project Structure

```
frontend/
├── app.py                    # Main entry point, authentication, tab routing
├── config.py                 # API endpoints, constants, timeout values
├── requirements.txt          # Dependencies (streamlit, requests, etc.)
├── components/
│   ├── __init__.py
│   ├── review_queue.py       # Review queue UI and interactions
│   ├── browse.py             # Browse/analytics UI
│   └── utils.py              # Shared helpers (API calls, formatting)
└── .streamlit/
    └── config.toml           # Streamlit config (theme, layout)
```

### 2.2 Data Flow

```
Streamlit App (port 8501)
  ↓ (HTTP requests with auth token)
FastAPI Backend (port 8000)
  ↓ (queries, filters)
DuckDB (data/finance.duckdb)
```

### 2.3 State Management

- **Authentication:** `st.session_state['auth_token']`, `st.session_state['username']`
- **Tab state:** `st.session_state['active_tab']` (review_queue or browse)
- **Review queue:** `st.session_state['page_num']` (pagination), `st.session_state['sort_order']` (asc/desc)
- **Browse filters:** `st.session_state['date_from']`, `st.session_state['date_to']`, `st.session_state['category_filter']`
- **Stateless by default:** Page reload clears all state except auth token

---

## 3. Authentication

### 3.1 Login Flow

1. App loads, checks `st.session_state['auth_token']`
2. If missing → show login form (username, password inputs, login button)
3. User submits → POST `/api/auth/login` with credentials
4. Backend validates against bcrypt-hashed passwords in DuckDB `users` table
5. On success → returns JWT or opaque session token
6. Streamlit stores token in session state, redirects to main app
7. On error → display error message, stay on login form

### 3.2 Token Management

- **Storage:** `st.session_state['auth_token']` (cleared on logout or page close)
- **Transmission:** Included in all API requests as `Authorization: Bearer {token}` header
- **Expiration:** Token expires after 24 hours (backend enforces); Streamlit checks and redirects to login if expired
- **No credential exposure:** Passwords never stored, logged, or transmitted in plaintext; tokens used for all subsequent requests

### 3.3 User Table (DuckDB)

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,  -- bcrypt hash
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Initial users seeded via migration script or .env variable (e.g., `INITIAL_USERS=rafael:password1,heloisa:password2`).

### 3.4 Backend Auth Endpoints

- **POST `/api/auth/login`**
  - Request: `{ "username": "...", "password": "..." }`
  - Response: `{ "token": "...", "username": "...", "expires_in": 86400 }`
  - Errors: 401 on invalid credentials, 400 on malformed request

- **POST `/api/auth/logout`**
  - Request: `Authorization: Bearer {token}`
  - Response: `{ "message": "logged out" }`

---

## 4. Review Queue Tab (Default/Home)

**Important:** All transactions are receipt-level or bank statement row-level. A single receipt or bank transaction = one entry. We do NOT break down receipts into product line items. Example: a Whole Foods receipt with multiple items is stored as a single $150 transaction (not itemized).

### 4.1 Layout

```
[Logo/Title] 
[Review Queue | Browse]  ← tabs
────────────────────────────────────

[Check for new emails]  [Sort: Most Recent ▼] [Asc/Desc]

[Transaction List]
────────────────────────────────────
| Date       | Amount | Confidence | Category | Merchant | Description | [Edit] [✓] [✗] |
| 2026-06-03 | $45.99 | 92%        | Groceries| Whole Foods | groceries | [Edit] [✓] [✗] |
| 2026-06-02 | $120   | 45% ⚠️     | (empty)  | (empty)  | (empty)     | [Edit] [✓] [✗] |
...
```

### 4.2 Features

**Sorting:**
- Default: most recent first
- Sort dropdown: "Date (newest first)", "Date (oldest first)", "Amount (high to low)", "Amount (low to high)", "Confidence (high to low)"
- Dropdown state persisted in `st.session_state['sort_order']`

**Pagination:**
- Show 10 transactions per page
- Next/Previous buttons at bottom
- Page number in `st.session_state['page_num']`

**Per-Transaction Display:**
- **Date**: email received timestamp
- **Amount**: extracted transaction amount
- **Confidence**: Gemini extraction confidence score (0-100%), displayed as percentage
  - Low confidence (< 60%): warning badge 🔶
  - Medium (60-80%): neutral
  - High (> 80%): ✓ check mark
- **Category**: extracted category (or placeholder if extraction failed)
- **Merchant**: extracted merchant name
- **Description**: extracted transaction description
- **Actions**: [Edit] [Approve ✓] [Reject ✗]

**Edit Mode:**
- Click [Edit] on a transaction → inline form appears
- User can modify: category, merchant, amount, description
- [Cancel] and [Save] buttons
- On save → PATCH `/api/transactions/{id}` with updated fields
- On success → form closes, updated values display in table

**Approve/Reject:**
- [✓] Approve → POST `/api/transactions/{id}/approve`
  - On success: transaction moves out of pending (disappears from queue), show toast "Approved!"
- [✗] Reject → POST `/api/transactions/{id}/reject`
  - On success: transaction marked as rejected (removed from queue), show toast "Rejected"
  - Optional: reason field (Phase 3+)

**Check for New Emails:**
- Button at top: "🔄 Check for new emails"
- On click → POST `/api/transactions/poll_email`
- Show loading spinner while checking
- On success → show toast "Found X new transactions" and refresh the list
- On failure → show error banner "Failed to check emails. {error message}"

**Error Handling:**
- Empty state: "No pending transactions! ✓" (when queue is empty)
- API errors: Display error banner with retry button
- Network timeout: Show error, allow user to retry

### 4.3 Backend Endpoints

- **GET `/api/transactions/pending?sort_by=date&sort_order=desc&page=1&limit=10`**
  - Returns: paginated list of pending transactions
  - Fields: id, date, amount, confidence, category, merchant, description, status

- **PATCH `/api/transactions/{id}`**
  - Request: `{ "category": "...", "merchant": "...", "amount": ..., "description": "..." }`
  - Response: updated transaction object

- **POST `/api/transactions/{id}/approve`**
  - Request: `Authorization: Bearer {token}`
  - Response: `{ "message": "approved", "transaction_id": id, "status": "approved" }`

- **POST `/api/transactions/{id}/reject`**
  - Request: `Authorization: Bearer {token}`
  - Response: `{ "message": "rejected", "transaction_id": id, "status": "rejected" }`

- **POST `/api/transactions/poll_email`**
  - Request: `Authorization: Bearer {token}`
  - Response: `{ "new_transactions": 3, "errors": [] }`
  - Errors: `{ "errors": ["Gmail API rate limit exceeded"] }`

---

## 5. Browse Tab

### 5.1 Layout

```
[Review Queue | Browse]

[Date Range: From [picker] To [picker]] [Category: All ▼] [Export CSV]

┌─────────────────────────────────────┐
│ Spending by Category (Pie Chart)     │
│                                      │
│  Groceries: 40% ████████████████     │
│  Dining: 25% ██████████             │
│  Transport: 20% █████████           │
│  Other: 15% ███████                 │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Spending Trends (12 weeks)           │
│  Amount ($)                          │
│  600 ┤     ╱╲                        │
│  500 ┤    ╱  ╲    ╱╲                 │
│  400 ┤   ╱    ╲  ╱  ╲                │
│       └────────────────               │
│       Week 1  2  3  4 ...            │
└─────────────────────────────────────┘

[Transaction List]
────────────────────────────────────
| Date       | Merchant | Amount | Category |
| 2026-06-03 | Whole Foods | $45.99 | Groceries |
...
```

### 5.2 Features

**Charts:**
- **Spending by Category**: Pie chart showing % of total spending in each category
  - Built with Streamlit's `st.plotly_chart()` or similar
  - Data from `GET /api/analytics/by_category?date_from=...&date_to=...`
  
- **Time Trends**: Line or bar chart showing spending over past 12 weeks
  - X-axis: week; Y-axis: total spending
  - Data from `GET /api/analytics/trends?weeks=12&date_from=...&date_to=...`

**Filters:**
- **Date Range:** Date pickers for start/end date
  - Default: last 12 weeks (or all data if < 12 weeks exist)
  - State: `st.session_state['date_from']`, `st.session_state['date_to']`
  - On change: refetch charts and table

- **Category Filter:** Optional dropdown (Phase 2 MVP doesn't require this, but structure for it)
  - Options: "All", "Groceries", "Dining", etc.
  - Filters transaction list only (not charts, for now)

**Transaction List:**
- Searchable/sortable table: date, merchant, amount, category
- Rows are read-only (no editing in browse view)
- Default sort: date (newest first)

**Export:**
- Button: "📥 Export as CSV"
- On click → call backend for full export, download file
- Exported file: `transactions_<date>.csv` with columns: date, merchant, amount, category, description

**Empty State:**
- If no transactions in date range: "No transactions found for this period."

### 5.3 Backend Endpoints

- **GET `/api/transactions/processed?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&sort_by=date&sort_order=desc`**
  - Returns: processed (approved) transactions
  - Fields: id, date, amount, category, merchant, description

- **GET `/api/analytics/by_category?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`**
  - Returns: `{ "categories": [{ "name": "Groceries", "amount": 450.99, "pct": 40 }, ...] }`

- **GET `/api/analytics/trends?weeks=12`**
  - Returns: `{ "weeks": [{ "week_start": "2026-04-22", "total_spending": 520 }, ...] }`

- **GET `/api/transactions/export?date_from=...&date_to=...&format=csv`**
  - Returns: CSV file as attachment

---

## 6. Error Handling

### 6.1 API Errors

| Scenario | Display | Action |
|----------|---------|--------|
| Network timeout | Error banner: "Connection timeout. [Retry]" | Show retry button |
| 401 Unauthorized (token expired/invalid) | Redirect to login page | Clear session, force re-auth |
| 400 Bad Request | Toast: "Invalid input: {error message}" | Stay on current page |
| 500 Server Error | Error banner: "Server error. [Retry]" | Show retry button |
| Gmail API error (check emails fails) | Toast: "Failed to check emails: {detail}" | Stay in queue, let user retry |

### 6.2 Data Edge Cases

| Scenario | Display |
|----------|---------|
| Empty review queue | "No pending transactions. ✓" |
| Low-confidence extraction (< 60%) | 🔶 warning badge, fields may be empty/placeholder |
| Extraction failure (no data extracted) | Show empty/placeholder fields (Merchant: "—", Amount: "—"), user fills in |
| Empty browse results | "No transactions found for this period." |
| Charts with no data | Show empty chart placeholder |

---

## 7. Security Considerations

- **Password hashing:** All passwords hashed with bcrypt before storage
- **Token validation:** Backend validates token on every request
- **HTTPS required:** In production, enforce HTTPS to prevent token interception
- **No credential logging:** Passwords never logged in request/response logs
- **Session timeout:** Tokens expire after 24 hours; users re-authenticate
- **CSRF protection:** Streamlit handles CSRF by default (stateless, POST-only for mutations)
- **Input validation:** Backend validates all user inputs (category, amount, etc.)

---

## 8. Testing Strategy

### 8.1 Manual Testing (Phase 2)

- **Login:** Verify correct/incorrect credentials
- **Review Queue:** 
  - Add, approve, reject transactions
  - Edit transaction fields
  - Check for new emails (mock endpoint)
  - Sort, pagination
  - Low-confidence transactions display warning
- **Browse:** 
  - Verify charts render with sample data
  - Export CSV works
  - Date filters work
- **Error handling:** Break network, mock API errors, verify error messages

### 8.2 Future (Phase 3+)

- Unit tests for utils.py (formatting, API helpers)
- Integration tests with mock FastAPI backend
- E2E tests with Streamlit testing library

---

## 9. Dependencies

```
streamlit==1.28.0
requests==2.31.0
plotly==5.17.0  # for charts
python-dateutil==2.8.2
```

Backend (already exist):
- FastAPI
- bcrypt (for password hashing)
- DuckDB
- JWT/session token library

---

## 10. Success Criteria

Phase 2 is complete when:
- ✓ Login form works (create users, bcrypt hashing, token return)
- ✓ Review queue displays pending transactions
- ✓ User can approve/reject/edit transactions
- ✓ "Check for new emails" button triggers backend poller
- ✓ Browse tab shows spending by category and trends
- ✓ Export CSV works
- ✓ All API calls include auth header
- ✓ Error states handled gracefully
- ✓ Manual testing passes (no crashes, flows work end-to-end)

---

## 11. Future Work (Phase 3+)

- Manual receipt upload flow
- Bulk approve/reject actions
- Transaction notes/comments
- Category management UI
- Recurring transaction detection
- Budget alerts
- Multi-user dashboard
