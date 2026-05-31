import os
import base64
import json
import re
from pathlib import Path
from decimal import Decimal
import google.generativeai as genai
from dotenv import load_dotenv
from ..models import ExtractionResult, ExtractedTransaction, Currency
from datetime import date

load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

EXTRACTION_PROMPT = """
You are a financial data extraction assistant. Analyze this bank statement, receipt, or financial document.

Extract ALL transactions visible. For each transaction return a JSON object with:
- "date": ISO format (YYYY-MM-DD) or null if unclear
- "merchant": business/payee name, cleaned up (no account numbers), or null
- "amount": numeric value, positive for credits/income, negative for debits/expenses. null if unclear
- "currency": one of EUR, USD, GBP, BRL, CHF, PLN, CZK. Detect from document, default EUR
- "confidence": float 0.0-1.0 reflecting how certain you are about this transaction's data
- "notes": any uncertainty or ambiguity to flag, or null

Also detect the bank name if visible.

Respond with ONLY valid JSON in this exact structure:
{
  "bank_detected": "Bank Name or null",
  "extraction_notes": "any overall notes or null",
  "transactions": [ ... ]
}
"""


def extract_from_bytes(
    file_bytes: bytes,
    filename: str,
    mime_type: str,
) -> ExtractionResult:
    """Extract transactions from image or PDF bytes using Gemini Flash."""
    model = genai.GenerativeModel("gemini-2.0-flash")

    # Gemini accepts inline image data or uploaded files
    # For images: use inline_data part
    # For PDFs: use inline_data with application/pdf mime type
    part = {
        "inline_data": {
            "mime_type": mime_type,
            "data": base64.b64encode(file_bytes).decode(),
        }
    }

    response = model.generate_content([EXTRACTION_PROMPT, part])
    raw_text = response.text.strip()

    # Strip markdown code fences if present
    raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
    raw_text = re.sub(r"\n?```$", "", raw_text)

    data = json.loads(raw_text)

    transactions = []
    for t in data.get("transactions", []):
        amount = Decimal(str(t["amount"])) if t.get("amount") is not None else None
        tx_date = None
        if t.get("date"):
            try:
                tx_date = date.fromisoformat(t["date"])
            except ValueError:
                pass

        currency = Currency.EUR
        if t.get("currency"):
            try:
                currency = Currency(t["currency"].upper())
            except ValueError:
                pass

        transactions.append(
            ExtractedTransaction(
                date=tx_date,
                merchant=t.get("merchant"),
                amount=amount,
                currency=currency,
                confidence=float(t["confidence"]) if t.get("confidence") is not None else 0.5,
                notes=t.get("notes"),
            )
        )

    return ExtractionResult(
        transactions=transactions,
        source_file=filename,
        bank_detected=data.get("bank_detected"),
        extraction_notes=data.get("extraction_notes"),
    )


def get_mime_type(filename: str) -> str:
    """Infer MIME type from filename extension."""
    ext = Path(filename).suffix.lower()
    return {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "image/png")
