# Gemini Extraction + Upload UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire up real Gemini Flash vision extraction and add a manual file upload tab to the Streamlit frontend, completing the end-to-end pipeline: upload PDF/image → extract transactions → land in review queue with source document attached.

**Architecture:** The backend extractor (`backend/ingestion/extractor.py`) sends file bytes to Gemini 2.0 Flash via the `google-generativeai` SDK, parses the structured JSON response into `ExtractionResult`, and returns it. The upload router (`backend/routers/upload.py`) already calls the extractor and stores results — it also needs to store the uploaded file as a document BLOB so the review queue doc viewer can display it. The frontend gets a new "Upload" tab with a file picker, owner selector, and result summary.

**Tech Stack:** Python `google-generativeai` SDK, FastAPI `UploadFile`, Streamlit `st.file_uploader`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/ingestion/extractor.py` | Modify | Real Gemini API call, JSON parsing, fallback |
| `backend/routers/upload.py` | Modify | Store uploaded file as document BLOB after extraction |
| `backend/requirements.txt` | Modify | Add `google-generativeai` |
| `frontend/components/upload_tab.py` | Create | Upload UI component |
| `frontend/app.py` | Modify | Add Upload tab |
| `frontend/config.py` | Modify | Add upload endpoint key |
| `.env.example` | Create | Document required env vars |

---

## Task 1: Add Gemini dependency

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add google-generativeai to requirements**

Edit `backend/requirements.txt` to add:
```
google-generativeai==0.8.3
python-multipart==0.0.9
```

(`python-multipart` is required by FastAPI for `UploadFile` form parsing — verify it's not already present.)

- [ ] **Step 2: Install dependency**

```bash
pip install google-generativeai==0.8.3
```

Expected: installs without error.

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore(deps): add google-generativeai for Gemini extraction"
```

---

## Task 2: Create .env.example

**Files:**
- Create: `.env.example`

- [ ] **Step 1: Create .env.example**

Create `.env.example` at project root:
```
# Required for Gemini extraction
GEMINI_API_KEY=your-gemini-api-key-here

# Optional overrides
CONFIDENCE_THRESHOLD=0.90
DB_PATH=data/finance.db
GMAIL_CREDENTIALS_PATH=credentials.json
```

- [ ] **Step 2: Verify .env.example is not gitignored**

Check `.gitignore` — `.env.example` must NOT be ignored (only `.env` should be).

- [ ] **Step 3: Commit**

```bash
git add .env.example
git commit -m "chore: add .env.example documenting required env vars"
```

---

## Task 3: Implement Gemini extractor

**Files:**
- Modify: `backend/ingestion/extractor.py`

The extractor receives file bytes + mime type, calls Gemini Flash with a structured prompt, parses the JSON response into `ExtractionResult`. Falls back to empty result (not error) if API key missing or call fails, so test mode still works.

- [ ] **Step 1: Replace extractor with Gemini implementation**

Overwrite `backend/ingestion/extractor.py` with:

```python
"""Financial document extraction using Google Gemini Flash."""
import json
import logging
import os
from ..models import ExtractionResult, ExtractedTransaction, Currency

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.0-flash"

EXTRACTION_PROMPT = """You are a financial document parser. Extract ALL transactions from this bank statement or receipt.

Return ONLY valid JSON in this exact format — no markdown, no explanation:
{
  "bank": "bank name or null",
  "transactions": [
    {
      "date": "YYYY-MM-DD",
      "merchant": "merchant or description",
      "amount": 12.34,
      "currency": "EUR",
      "confidence": 0.95,
      "notes": "optional note or null"
    }
  ]
}

Rules:
- amount is always positive (expenses and income both positive)
- currency: EUR, USD, GBP, BRL, CHF, PLN, or CZK — default EUR
- confidence: 0.0-1.0 (how certain you are this is a real transaction)
- date: use YYYY-MM-DD, infer year from context if not shown
- If you cannot read the document clearly, return {"bank": null, "transactions": []}
"""


def extract_from_bytes(
    file_bytes: bytes,
    filename: str,
    mime_type: str,
) -> ExtractionResult:
    """Extract transactions from file bytes using Gemini Flash."""
    if not GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not set — extraction disabled (test mode)")
        return ExtractionResult(
            transactions=[],
            source_file=filename,
            bank_detected=None,
            extraction_notes="Extraction disabled: GEMINI_API_KEY not configured",
        )

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(MODEL)

        blob = {"mime_type": mime_type, "data": file_bytes}
        response = model.generate_content([EXTRACTION_PROMPT, blob])
        raw = response.text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Gemini returned invalid JSON: %s", e)
        return ExtractionResult(
            transactions=[],
            source_file=filename,
            bank_detected=None,
            extraction_notes=f"Parse error: {e}",
        )
    except Exception as e:
        logger.error("Gemini extraction failed: %s", e)
        return ExtractionResult(
            transactions=[],
            source_file=filename,
            bank_detected=None,
            extraction_notes=f"Extraction error: {e}",
        )

    transactions = []
    for item in data.get("transactions", []):
        try:
            currency_str = item.get("currency", "EUR").upper()
            try:
                currency = Currency(currency_str)
            except ValueError:
                currency = Currency.EUR

            tx = ExtractedTransaction(
                date=item.get("date"),
                merchant=item.get("merchant"),
                amount=item.get("amount"),
                currency=currency,
                confidence=float(item.get("confidence", 0.5)),
                notes=item.get("notes"),
            )
            transactions.append(tx)
        except Exception as e:
            logger.warning("Skipping malformed transaction %s: %s", item, e)
            continue

    return ExtractionResult(
        transactions=transactions,
        source_file=filename,
        bank_detected=data.get("bank"),
        extraction_notes=None,
    )


def get_mime_type(filename: str) -> str:
    """Get MIME type from filename."""
    name = filename.lower()
    if name.endswith(".pdf"):
        return "application/pdf"
    elif name.endswith(".png"):
        return "image/png"
    elif name.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    elif name.endswith(".webp"):
        return "image/webp"
    return "application/octet-stream"
```

- [ ] **Step 2: Smoke test without API key (test mode)**

Start backend and POST a file without GEMINI_API_KEY set:

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/any.png" \
  -F "owner=Rafael"
```

Expected response:
```json
{"stored": 0, "pending_review": 0, "transactions": []}
```

(No crash, just empty result with notes logged.)

- [ ] **Step 3: Commit**

```bash
git add backend/ingestion/extractor.py
git commit -m "feat(extractor): implement Gemini Flash extraction with test-mode fallback"
```

---

## Task 4: Store uploaded file as document BLOB

**Files:**
- Modify: `backend/routers/upload.py`

After extraction, store the raw uploaded bytes in the `documents` table linked to each extracted transaction. This enables the review queue doc viewer to show the source file.

- [ ] **Step 1: Update upload router to store documents**

Replace the `upload_file` function body in `backend/routers/upload.py`:

```python
import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, UploadFile, Form, HTTPException

from ..db.client import get_connection, generate_id
from ..ingestion.extractor import extract_from_bytes, get_mime_type
from ..models import Owner, Status

router = APIRouter()
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.90"))
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "application/pdf", "image/webp"}


@router.post("")
async def upload_file(
    file: UploadFile,
    owner: Optional[str] = Form(None),
):
    owner_enum = None
    if owner:
        try:
            owner_enum = Owner(owner)
        except ValueError:
            raise HTTPException(400, f"Invalid owner '{owner}'. Must be Rafael, Heloisa, or Shared.")

    mime = get_mime_type(file.filename)
    if mime not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, f"Unsupported file type: {file.filename}")

    file_bytes = await file.read()
    result = extract_from_bytes(file_bytes, file.filename, mime)

    conn = get_connection()
    stored, pending = 0, 0
    inserted = []

    for tx in result.transactions:
        if tx.date is None or tx.amount is None or tx.merchant is None:
            continue
        status = Status.approved if tx.confidence >= CONFIDENCE_THRESHOLD else Status.pending
        tx_id = generate_id()
        conn.execute(
            """INSERT INTO transactions
               (id, date, merchant, amount, currency, category, owner,
                confidence, status, source_file, bank, raw_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [tx_id, tx.date, tx.merchant, float(tx.amount), tx.currency.value,
             None, owner_enum.value if owner_enum else None,
             tx.confidence, status.value, file.filename,
             result.bank_detected, None, datetime.now(timezone.utc)],
        )

        # Attach source document to each extracted transaction
        conn.execute(
            """INSERT INTO documents (id, transaction_id, filename, mime_type, file_blob, uploaded_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [generate_id(), tx_id, file.filename, mime, file_bytes,
             datetime.now(timezone.utc).isoformat()]
        )

        stored += 1
        if status == Status.pending:
            pending += 1
        inserted.append({"id": tx_id, "merchant": tx.merchant,
                         "amount": float(tx.amount), "status": status.value,
                         "confidence": tx.confidence})

    conn.commit()
    return {
        "stored": stored,
        "pending_review": pending,
        "transactions": inserted,
        "notes": result.extraction_notes,
    }
```

- [ ] **Step 2: Verify no regression (test mode)**

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/any.png"
```

Expected: `{"stored": 0, "pending_review": 0, "transactions": [], "notes": "Extraction disabled..."}` — no crash.

- [ ] **Step 3: Commit**

```bash
git add backend/routers/upload.py
git commit -m "feat(upload): store uploaded file as document BLOB per extracted transaction"
```

---

## Task 5: Add upload endpoint to frontend config

**Files:**
- Modify: `frontend/config.py`

- [ ] **Step 1: Add upload endpoint**

In `frontend/config.py`, add to the `ENDPOINTS` dict:
```python
"upload": f"{API_BASE_URL}/api/upload",
```

- [ ] **Step 2: Commit**

```bash
git add frontend/config.py
git commit -m "chore(frontend): add upload endpoint to config"
```

---

## Task 6: Create upload tab component

**Files:**
- Create: `frontend/components/upload_tab.py`

- [ ] **Step 1: Create upload component**

Create `frontend/components/upload_tab.py`:

```python
import streamlit as st
import requests
from config import ENDPOINTS, API_TIMEOUT

OWNER_OPTIONS = ["(not specified)", "Rafael", "Heloisa", "Shared"]
ACCEPTED_TYPES = ["pdf", "png", "jpg", "jpeg", "webp"]


def show_upload_tab(token: str):
    """Upload a bank statement or receipt for Gemini extraction."""
    st.subheader("Upload Statement or Receipt")
    st.caption("Supported formats: PDF, PNG, JPG, WEBP — Portuguese bank statements and receipts")

    owner_label = st.selectbox("Assign to", OWNER_OPTIONS)
    owner = None if owner_label == "(not specified)" else owner_label

    uploaded = st.file_uploader(
        "Choose file",
        type=ACCEPTED_TYPES,
        help="Upload a bank statement PDF or a receipt image",
    )

    if uploaded is None:
        st.info("No file selected. Upload a bank statement or receipt to extract transactions.")
        return

    st.write(f"**File:** {uploaded.name}  |  **Size:** {len(uploaded.getvalue()) / 1024:.1f} KB")

    if st.button("Extract transactions", type="primary", use_container_width=True):
        _run_extraction(token, uploaded, owner)


def _run_extraction(token: str, uploaded, owner: str | None):
    """POST file to backend, display results."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with st.spinner("Sending to Gemini for extraction... this may take 10-30 seconds"):
        try:
            files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream")}
            data = {"owner": owner} if owner else {}
            resp = requests.post(
                ENDPOINTS["upload"],
                files=files,
                data=data,
                headers=headers,
                timeout=60,  # Gemini can be slow on large PDFs
            )
        except requests.Timeout:
            st.error("Request timed out. The file may be too large or Gemini is slow. Try again.")
            return
        except requests.RequestException as e:
            st.error(f"Network error: {e}")
            return

    if resp.status_code == 400:
        st.error(resp.json().get("detail", "Invalid file or request"))
        return
    if resp.status_code >= 500:
        st.error(f"Server error {resp.status_code}. Check backend logs.")
        return

    result = resp.json()
    stored = result.get("stored", 0)
    pending = result.get("pending_review", 0)
    transactions = result.get("transactions", [])
    notes = result.get("notes")

    if notes:
        st.warning(f"Note: {notes}")

    if stored == 0:
        st.warning("No transactions extracted. Check that GEMINI_API_KEY is set and the file is readable.")
        return

    st.success(f"Extracted **{stored}** transaction(s) — **{pending}** sent to review queue")

    if transactions:
        st.markdown("### Extracted transactions")
        for tx in transactions:
            status_icon = "🟡" if tx["status"] == "pending" else "✅"
            st.write(
                f"{status_icon} **{tx['merchant']}** — "
                f"€{tx['amount']:.2f} "
                f"(confidence: {tx['confidence']:.0%})"
            )

    if pending > 0:
        st.info(f"{pending} transaction(s) need review — go to the **Review Queue** tab.")
```

- [ ] **Step 2: Commit**

```bash
git add frontend/components/upload_tab.py
git commit -m "feat(frontend): add upload tab component for Gemini extraction"
```

---

## Task 7: Wire upload tab into main app

**Files:**
- Modify: `frontend/app.py`

- [ ] **Step 1: Read current app.py tab structure**

Open `frontend/app.py` and find the `show_main_app()` function with the `st.tabs` call.

- [ ] **Step 2: Add Upload tab**

Import the new component at the top of `app.py`:
```python
from components.upload_tab import show_upload_tab
```

Find the tabs definition (currently `["Review Queue", "Browse"]`) and expand it:
```python
tab1, tab2, tab3 = st.tabs(["Review Queue", "Browse", "Upload"])

with tab1:
    show_review_queue(st.session_state["auth_token"])

with tab2:
    show_browse(st.session_state["auth_token"])

with tab3:
    show_upload_tab(st.session_state["auth_token"])
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app.py
git commit -m "feat(frontend): add Upload tab to main app"
```

---

## Task 8: End-to-end verification

- [ ] **Step 1: Set GEMINI_API_KEY in .env**

Create or update `.env` in project root:
```
GEMINI_API_KEY=<your-key-from-aistudio.google.com>
```

- [ ] **Step 2: Restart backend**

Stop existing uvicorn process and restart:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Expected in logs: no errors on startup.

- [ ] **Step 3: Open Streamlit and test upload**

Navigate to http://localhost:8501 → log in → go to **Upload** tab.

Upload a real Portuguese bank statement PDF or receipt image:
- Select owner (e.g. Rafael)
- Click "Extract transactions"
- Expected: spinner for 10-30s, then success message with list of extracted transactions

- [ ] **Step 4: Verify transactions appear in Review Queue**

Switch to **Review Queue** tab. Newly extracted pending transactions should appear.

- [ ] **Step 5: Verify source document attached**

Click "📄 Source" on a newly extracted transaction. The original uploaded file should display in the right panel with download button.

- [ ] **Step 6: Test without API key (regression)**

Temporarily unset `GEMINI_API_KEY`, restart backend, upload a file.
Expected: "No transactions extracted. Check that GEMINI_API_KEY is set..." warning — no crash.

---

## Notes

- Gemini free tier: ~1500 requests/day, ~4MB per file — sufficient for personal use
- Large multi-page PDFs may take 30+ seconds — the upload component uses a 60s timeout
- The extractor prompt defaults to EUR currency — Gemini infers the correct currency from the document
- For Portuguese banks: Millennium BCP, Caixa Geral, Santander PT, BPI, Novo Banco all produce standard PDF statements that Gemini handles well
- If extraction quality is poor, tune the `EXTRACTION_PROMPT` in `extractor.py` — add bank-specific hints
