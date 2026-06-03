# Phase 2 Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Streamlit frontend with authentication, transaction review queue, and analytics browse tab connected to FastAPI backend.

**Architecture:** Component-based Streamlit app (port 8501) with modular components for auth, review queue, and browse. All API calls include bearer token auth. Transactions stored/viewed at receipt-level granularity. State management via `st.session_state`.

**Tech Stack:** Streamlit 1.28.0, Requests 2.31.0, Plotly 5.17.0, Python 3.10+

---

## Phase 2A: Project Setup & Config

### Task 1: Create frontend directory structure and requirements.txt

**Files:**
- Create: `frontend/requirements.txt`
- Create: `frontend/.streamlit/config.toml`
- Create: `frontend/config.py`
- Create: `frontend/components/__init__.py`

- [ ] **Step 1: Create frontend/.streamlit/ directory**

```powershell
New-Item -ItemType Directory -Path frontend\.streamlit -Force
```

- [ ] **Step 2: Write frontend/requirements.txt**

```
streamlit==1.28.0
requests==2.31.0
plotly==5.17.0
python-dateutil==2.8.2
```

- [ ] **Step 3: Write frontend/.streamlit/config.toml**

```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F0F0"
textColor = "#333333"
font = "sans serif"

[client]
showErrorDetails = true

[logger]
level = "info"
```

- [ ] **Step 4: Write frontend/config.py**

```python
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TIMEOUT = 10
TOKEN_EXPIRATION_HOURS = 24
PAGE_SIZE = 10

# API Endpoints
ENDPOINTS = {
    "login": f"{API_BASE_URL}/api/auth/login",
    "logout": f"{API_BASE_URL}/api/auth/logout",
    "pending_transactions": f"{API_BASE_URL}/api/transactions/pending",
    "update_transaction": f"{API_BASE_URL}/api/transactions",
    "approve_transaction": f"{API_BASE_URL}/api/transactions",
    "reject_transaction": f"{API_BASE_URL}/api/transactions",
    "poll_email": f"{API_BASE_URL}/api/transactions/poll_email",
    "processed_transactions": f"{API_BASE_URL}/api/transactions/processed",
    "analytics_by_category": f"{API_BASE_URL}/api/analytics/by_category",
    "analytics_trends": f"{API_BASE_URL}/api/analytics/trends",
    "export_transactions": f"{API_BASE_URL}/api/transactions/export",
}

# Categories for dropdown (populate dynamically from backend later)
CATEGORIES = [
    "Groceries",
    "Dining",
    "Transport",
    "Utilities",
    "Entertainment",
    "Healthcare",
    "Shopping",
    "Other",
]
```

- [ ] **Step 5: Write frontend/components/__init__.py**

```python
# Components package
```

- [ ] **Step 6: Commit**

```powershell
git add frontend/requirements.txt frontend/.streamlit/config.toml frontend/config.py frontend/components/__init__.py
git commit -m "feat: initialize Streamlit frontend project structure"
```

---

## Phase 2B: Authentication

### Task 2: Implement authentication utilities

**Files:**
- Create: `frontend/components/utils.py`

- [ ] **Step 1: Write frontend/components/utils.py**

```python
import requests
import streamlit as st
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, Any

from config import ENDPOINTS, API_TIMEOUT


def make_api_call(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    token: Optional[str] = None,
    params: Optional[Dict] = None,
) -> tuple[bool, Any]:
    """
    Make API call with error handling and auth token.
    Returns: (success: bool, response: dict or error message: str)
    """
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        if method.upper() == "GET":
            resp = requests.get(
                endpoint, headers=headers, params=params, timeout=API_TIMEOUT
            )
        elif method.upper() == "POST":
            resp = requests.post(
                endpoint, json=data, headers=headers, timeout=API_TIMEOUT
            )
        elif method.upper() == "PATCH":
            resp = requests.patch(
                endpoint, json=data, headers=headers, timeout=API_TIMEOUT
            )
        else:
            return False, "Unsupported HTTP method"

        # Handle 401 — token expired or invalid
        if resp.status_code == 401:
            st.session_state["auth_token"] = None
            st.session_state["username"] = None
            return False, "Session expired. Please log in again."

        # Handle other errors
        if resp.status_code >= 400:
            error_detail = resp.json().get("detail", resp.text)
            return False, f"Error {resp.status_code}: {error_detail}"

        return True, resp.json()

    except requests.Timeout:
        return False, "Connection timeout. Please try again."
    except requests.RequestException as e:
        return False, f"Network error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def login(username: str, password: str) -> tuple[bool, str]:
    """
    Attempt login with username/password.
    Returns: (success: bool, message: str)
    """
    success, response = make_api_call(
        "POST",
        ENDPOINTS["login"],
        data={"username": username, "password": password},
    )

    if success:
        st.session_state["auth_token"] = response.get("token")
        st.session_state["username"] = response.get("username")
        return True, "Login successful"
    else:
        return False, response


def logout():
    """Clear auth state."""
    token = st.session_state.get("auth_token")
    if token:
        make_api_call("POST", ENDPOINTS["logout"], token=token)
    st.session_state["auth_token"] = None
    st.session_state["username"] = None


def format_currency(amount: float) -> str:
    """Format number as USD currency."""
    return f"${amount:,.2f}"


def format_confidence(confidence: int) -> str:
    """Format confidence score with visual indicator."""
    if confidence < 60:
        return f"{confidence}% 🔶"
    elif confidence < 80:
        return f"{confidence}%"
    else:
        return f"{confidence}% ✓"


def format_date(date_str: str) -> str:
    """Format ISO date string to readable format."""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except:
        return date_str
```

- [ ] **Step 2: Commit**

```powershell
git add frontend/components/utils.py
git commit -m "feat: add authentication and API call utilities"
```

---

## Phase 2C: Main App & Login Flow

### Task 3: Implement main app.py with authentication flow

**Files:**
- Create: `frontend/app.py`

- [ ] **Step 1: Write frontend/app.py**

```python
import streamlit as st
from components.utils import login, logout
from components.review_queue import show_review_queue
from components.browse import show_browse

st.set_page_config(page_title="Household Finance Copilot", layout="wide")

# Initialize session state
if "auth_token" not in st.session_state:
    st.session_state["auth_token"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Review Queue"


def show_login():
    """Display login form."""
    st.title("🏠 Household Finance Copilot")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Login")

        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", use_container_width=True):
            if username and password:
                success, message = login(username, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Please enter username and password")


def show_main_app():
    """Display authenticated main app."""
    # Header
    col1, col2 = st.columns([1, 4])
    with col1:
        st.title("🏠 Household Finance Copilot")
    with col2:
        st.markdown(f"**Logged in as:** {st.session_state['username']}")
        if st.button("Logout", use_container_width=False):
            logout()
            st.rerun()

    st.markdown("---")

    # Tabs
    tab1, tab2 = st.tabs(["Review Queue", "Browse"])

    with tab1:
        show_review_queue(st.session_state["auth_token"])

    with tab2:
        show_browse(st.session_state["auth_token"])


# Main logic
if st.session_state["auth_token"]:
    show_main_app()
else:
    show_login()
```

- [ ] **Step 2: Commit**

```powershell
git add frontend/app.py
git commit -m "feat: add main app with login/logout and tab routing"
```

---

## Phase 2D: Review Queue Component

### Task 4: Implement review_queue.py with pending transaction display

**Files:**
- Create: `frontend/components/review_queue.py`

- [ ] **Step 1: Write frontend/components/review_queue.py (Part 1: Display & Interactions)**

```python
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from components.utils import (
    make_api_call,
    format_currency,
    format_confidence,
    format_date,
)
from config import ENDPOINTS, PAGE_SIZE


def show_review_queue(token: str):
    """Display review queue tab with pending transactions."""

    # Initialize session state for review queue
    if "page_num" not in st.session_state:
        st.session_state["page_num"] = 1
    if "sort_order" not in st.session_state:
        st.session_state["sort_order"] = "date_desc"

    # Sort dropdown
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        if st.button("🔄 Check for new emails", use_container_width=True):
            poll_emails(token)

    with col2:
        sort_options = {
            "Date (newest first)": "date_desc",
            "Date (oldest first)": "date_asc",
            "Amount (high to low)": "amount_desc",
            "Amount (low to high)": "amount_asc",
            "Confidence (high to low)": "confidence_desc",
        }
        selected_sort = st.selectbox(
            "Sort by:",
            list(sort_options.keys()),
            index=0,
            key="sort_select",
            label_visibility="collapsed",
        )
        st.session_state["sort_order"] = sort_options[selected_sort]

    st.markdown("---")

    # Fetch pending transactions
    success, response = fetch_pending_transactions(
        token, st.session_state["page_num"], st.session_state["sort_order"]
    )

    if not success:
        st.error(response)
        return

    transactions = response.get("transactions", [])
    total_count = response.get("total", 0)
    total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE

    # Empty state
    if not transactions:
        st.info("✓ No pending transactions! You're all caught up.")
        return

    # Display transactions
    display_transactions(token, transactions)

    st.markdown("---")

    # Pagination
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.session_state["page_num"] > 1:
            if st.button("← Previous"):
                st.session_state["page_num"] -= 1
                st.rerun()

    with col2:
        st.write(
            f"Page {st.session_state['page_num']} of {total_pages} "
            f"({total_count} total)"
        )

    with col3:
        if st.session_state["page_num"] < total_pages:
            if st.button("Next →"):
                st.session_state["page_num"] += 1
                st.rerun()


def fetch_pending_transactions(
    token: str, page: int, sort_order: str
) -> tuple[bool, dict]:
    """Fetch pending transactions from backend."""
    sort_by, order = parse_sort_order(sort_order)

    success, response = make_api_call(
        "GET",
        ENDPOINTS["pending_transactions"],
        token=token,
        params={
            "sort_by": sort_by,
            "sort_order": order,
            "page": page,
            "limit": PAGE_SIZE,
        },
    )

    return success, response


def parse_sort_order(sort_order: str) -> tuple[str, str]:
    """Convert UI sort string to API params."""
    mapping = {
        "date_desc": ("date", "desc"),
        "date_asc": ("date", "asc"),
        "amount_desc": ("amount", "desc"),
        "amount_asc": ("amount", "asc"),
        "confidence_desc": ("confidence", "desc"),
    }
    return mapping.get(sort_order, ("date", "desc"))


def display_transactions(token: str, transactions: list):
    """Display transactions as interactive table with edit/approve/reject."""

    for idx, tx in enumerate(transactions):
        with st.container(border=True):
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])

            with col1:
                st.write(f"**{format_date(tx['date'])}**")
            with col2:
                st.write(f"{format_currency(tx['amount'])}")
            with col3:
                st.write(format_confidence(tx.get("confidence", 0)))
            with col4:
                st.write(tx.get("category") or "—")
            with col5:
                st.write(tx.get("merchant") or "—")

            st.write(f"Description: {tx.get('description', '—')}")

            # Action buttons
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                if st.button("✏️ Edit", key=f"edit_{tx['id']}"):
                    st.session_state[f"edit_{tx['id']}"] = True

            with col_b:
                if st.button("✓ Approve", key=f"approve_{tx['id']}"):
                    approve_transaction(token, tx["id"])

            with col_c:
                if st.button("✗ Reject", key=f"reject_{tx['id']}"):
                    reject_transaction(token, tx["id"])

            # Edit form (inline)
            if st.session_state.get(f"edit_{tx['id']}", False):
                show_edit_form(token, tx)


def show_edit_form(token: str, tx: dict):
    """Display inline edit form for transaction."""
    st.write("**Edit Transaction**")

    col1, col2 = st.columns(2)
    with col1:
        category = st.text_input(
            "Category", value=tx.get("category", ""), key=f"cat_{tx['id']}"
        )
        amount = st.number_input(
            "Amount", value=tx["amount"], key=f"amt_{tx['id']}"
        )

    with col2:
        merchant = st.text_input(
            "Merchant", value=tx.get("merchant", ""), key=f"merch_{tx['id']}"
        )
        description = st.text_input(
            "Description",
            value=tx.get("description", ""),
            key=f"desc_{tx['id']}",
        )

    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("Save", key=f"save_{tx['id']}"):
            update_transaction(
                token,
                tx["id"],
                category=category,
                merchant=merchant,
                amount=amount,
                description=description,
            )

    with col_cancel:
        if st.button("Cancel", key=f"cancel_{tx['id']}"):
            st.session_state[f"edit_{tx['id']}"] = False
            st.rerun()


def poll_emails(token: str):
    """Poll for new emails."""
    with st.spinner("Checking for new emails..."):
        success, response = make_api_call(
            "POST", ENDPOINTS["poll_email"], token=token
        )

    if success:
        new_count = response.get("new_transactions", 0)
        if new_count > 0:
            st.success(f"✓ Found {new_count} new transaction(s)")
            st.session_state["page_num"] = 1  # Reset to first page
            st.rerun()
        else:
            st.info("No new transactions")
    else:
        st.error(f"Failed to check emails: {response}")


def update_transaction(
    token: str, tx_id: int, category: str, merchant: str, amount: float, description: str
):
    """Update transaction."""
    success, response = make_api_call(
        "PATCH",
        f"{ENDPOINTS['update_transaction']}/{tx_id}",
        data={
            "category": category,
            "merchant": merchant,
            "amount": amount,
            "description": description,
        },
        token=token,
    )

    if success:
        st.success("✓ Transaction updated")
        st.session_state[f"edit_{tx_id}"] = False
        st.rerun()
    else:
        st.error(f"Failed to update: {response}")


def approve_transaction(token: str, tx_id: int):
    """Approve transaction."""
    success, response = make_api_call(
        "POST",
        f"{ENDPOINTS['approve_transaction']}/{tx_id}/approve",
        token=token,
    )

    if success:
        st.success("✓ Approved")
        st.rerun()
    else:
        st.error(f"Failed to approve: {response}")


def reject_transaction(token: str, tx_id: int):
    """Reject transaction."""
    success, response = make_api_call(
        "POST",
        f"{ENDPOINTS['reject_transaction']}/{tx_id}/reject",
        token=token,
    )

    if success:
        st.success("✓ Rejected")
        st.rerun()
    else:
        st.error(f"Failed to reject: {response}")
```

- [ ] **Step 2: Commit**

```powershell
git add frontend/components/review_queue.py
git commit -m "feat: implement review queue with display, edit, approve/reject actions"
```

---

## Phase 2E: Browse & Analytics Component

### Task 5: Implement browse.py with charts, filters, and export

**Files:**
- Create: `frontend/components/browse.py`

- [ ] **Step 1: Write frontend/components/browse.py**

```python
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from components.utils import make_api_call, format_currency, format_date
from config import ENDPOINTS, CATEGORIES


def show_browse(token: str):
    """Display browse/analytics tab."""

    # Initialize session state
    if "date_from" not in st.session_state:
        st.session_state["date_from"] = datetime.now() - timedelta(weeks=12)
    if "date_to" not in st.session_state:
        st.session_state["date_to"] = datetime.now()
    if "category_filter" not in st.session_state:
        st.session_state["category_filter"] = "All"

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        date_from = st.date_input(
            "From:",
            value=st.session_state["date_from"],
            key="browse_from",
        )
        st.session_state["date_from"] = date_from

    with col2:
        date_to = st.date_input(
            "To:",
            value=st.session_state["date_to"],
            key="browse_to",
        )
        st.session_state["date_to"] = date_to

    with col3:
        category = st.selectbox(
            "Category:",
            ["All"] + CATEGORIES,
            index=0,
            key="browse_category",
        )
        st.session_state["category_filter"] = category

    export_col = st.columns(1)[0]
    with export_col:
        if st.button("📥 Export as CSV", use_container_width=False):
            export_csv(token, date_from, date_to)

    st.markdown("---")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Spending by Category")
        show_category_chart(token, date_from, date_to)

    with col2:
        st.subheader("Spending Trends (12 weeks)")
        show_trends_chart(token)

    st.markdown("---")

    # Transaction table
    st.subheader("Transactions")
    show_transaction_table(token, date_from, date_to, category)


def show_category_chart(token: str, date_from, date_to):
    """Display pie chart of spending by category."""
    success, response = make_api_call(
        "GET",
        ENDPOINTS["analytics_by_category"],
        token=token,
        params={
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
        },
    )

    if not success:
        st.error(f"Failed to load chart: {response}")
        return

    categories = response.get("categories", [])

    if not categories:
        st.info("No data for this period")
        return

    cat_names = [c["name"] for c in categories]
    cat_amounts = [c["amount"] for c in categories]

    fig = go.Figure(
        data=[go.Pie(labels=cat_names, values=cat_amounts, textinfo="label+percent")]
    )
    fig.update_layout(height=400)

    st.plotly_chart(fig, use_container_width=True)


def show_trends_chart(token: str):
    """Display line chart of spending trends."""
    success, response = make_api_call(
        "GET",
        ENDPOINTS["analytics_trends"],
        token=token,
        params={"weeks": 12},
    )

    if not success:
        st.error(f"Failed to load chart: {response}")
        return

    weeks = response.get("weeks", [])

    if not weeks:
        st.info("No data for this period")
        return

    week_labels = [w["week_start"] for w in weeks]
    week_amounts = [w["total_spending"] for w in weeks]

    fig = go.Figure(
        data=[go.Scatter(x=week_labels, y=week_amounts, mode="lines+markers")]
    )
    fig.update_layout(
        title="",
        xaxis_title="Week",
        yaxis_title="Total Spending ($)",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def show_transaction_table(token: str, date_from, date_to, category_filter: str):
    """Display processed transactions table."""
    success, response = make_api_call(
        "GET",
        ENDPOINTS["processed_transactions"],
        token=token,
        params={
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "sort_by": "date",
            "sort_order": "desc",
        },
    )

    if not success:
        st.error(f"Failed to load transactions: {response}")
        return

    transactions = response.get("transactions", [])

    # Filter by category if selected
    if category_filter != "All":
        transactions = [tx for tx in transactions if tx.get("category") == category_filter]

    if not transactions:
        st.info("No transactions found for this period")
        return

    # Display as table
    df = pd.DataFrame(
        [
            {
                "Date": format_date(tx["date"]),
                "Merchant": tx.get("merchant", "—"),
                "Amount": format_currency(tx["amount"]),
                "Category": tx.get("category", "—"),
            }
            for tx in transactions
        ]
    )

    st.dataframe(df, use_container_width=True, hide_index=True)


def export_csv(token: str, date_from, date_to):
    """Export transactions as CSV."""
    success, response = make_api_call(
        "GET",
        ENDPOINTS["export_transactions"],
        token=token,
        params={
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "format": "csv",
        },
    )

    if not success:
        st.error(f"Failed to export: {response}")
        return

    # Response should be CSV content
    csv_content = response

    filename = f"transactions_{datetime.now().strftime('%Y%m%d')}.csv"

    st.download_button(
        label="📥 Download CSV",
        data=csv_content,
        file_name=filename,
        mime="text/csv",
    )
```

- [ ] **Step 2: Commit**

```powershell
git add frontend/components/browse.py
git commit -m "feat: implement browse tab with analytics charts, filters, and CSV export"
```

---

## Phase 2F: Testing & Verification

### Task 6: Manual testing checklist and bug fixes

**Files:**
- No new files (testing phase)

- [ ] **Step 1: Start FastAPI backend**

Verify backend is running on port 8000:

```powershell
cd backend
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

- [ ] **Step 2: Start Streamlit frontend**

```powershell
cd frontend
streamlit run app.py --logger.level=debug
```

- [ ] **Step 3: Test login flow**

- Open http://localhost:8501 in browser
- Test login with incorrect credentials → should show error
- Test login with correct credentials (seeded user) → should display main app
- Verify token stored in session state (check browser console for `st.session_state`)
- Click logout → verify redirected to login form

- [ ] **Step 4: Test Review Queue**

- Verify pending transactions display with all fields (date, amount, confidence, category, merchant, description)
- Verify confidence badge shows 🔶 for < 60%, ✓ for > 80%
- Test approve button → verify transaction disappears from list
- Test reject button → verify transaction disappears from list
- Test edit button → inline form appears → edit fields → save → verify updates in table
- Test sort dropdown → verify transactions re-order correctly
- Test pagination → click Next/Previous → verify pages load correctly
- Test "Check for new emails" button → if backend has new data, verify list updates

Expected: No crashes, all buttons functional, data displays correctly

- [ ] **Step 5: Test Browse tab**

- Click Browse tab → verify charts render (pie chart + line chart)
- Verify category chart shows correct percentages
- Verify trends chart shows 12-week data
- Test date filter → change from/to dates → verify charts update
- Test category filter → select category → verify table filters
- Test CSV export button → verify download works
- Verify transaction table displays with correct formatting

Expected: All charts render, filters work, export downloads

- [ ] **Step 6: Test error handling**

- Stop backend
- Try login → should show network error
- Try any action → should show "Connection timeout" or similar
- Start backend again → verify app recovers

- [ ] **Step 7: Document any bugs found**

If issues found, note them with:
- Exact reproduction steps
- Expected vs actual behavior
- Suspected root cause

- [ ] **Step 8: Fix critical bugs**

High priority (blocking use):
- Login not working
- API calls not authenticated (no token in headers)
- Charts not rendering
- Approve/reject not working

Medium priority (poor UX):
- Formatting issues
- Missing error messages
- Pagination bugs

Do not fix polish/cosmetic issues yet.

- [ ] **Step 9: Final verification**

Re-run all tests from Step 3-7. Confirm:
- ✓ Login works
- ✓ Review queue displays and actions work
- ✓ Browse charts render
- ✓ Export works
- ✓ Error handling graceful

- [ ] **Step 10: Commit**

```powershell
git add frontend/
git commit -m "feat: complete Phase 2 frontend with manual testing passing"
```

---

## Success Criteria

Phase 2 implementation complete when:

- ✓ All files created (app.py, config.py, utils.py, review_queue.py, browse.py, requirements.txt, config.toml)
- ✓ Login/logout flow functional with token auth
- ✓ Review Queue displays pending transactions, approve/reject/edit work
- ✓ Browse tab shows analytics, filters work, CSV export works
- ✓ All API calls include authorization header
- ✓ Error handling for network/auth failures
- ✓ Manual testing passes (all flows work, no crashes)
- ✓ Code committed to git with clear commit messages

---

## Known Limitations (Phase 2 MVP)

- No unit tests (deferred to Phase 3)
- Category filter in browse does not filter charts (only table)
- No bulk approve/reject (single transaction only)
- No transaction notes/comments
- Export returns raw data (no formatting validation)
- Admin user management not implemented (hardcoded seeded users)

