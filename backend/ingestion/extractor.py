"""Financial document extraction using Google Gemini Flash."""
import json
import logging
import os
from ..models import ExtractionResult, ExtractedTransaction, Currency

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash"

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
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                EXTRACTION_PROMPT,
            ],
        )
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
