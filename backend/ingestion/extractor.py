"""Financial document extraction using Groq (text + vision)."""
import base64
import json
import logging
import os
from ..models import ExtractionResult, ExtractedTransaction, Currency

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TEXT_MODEL = os.getenv("GROQ_TEXT_MODEL", "llama-3.3-70b-versatile")
VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview")
MIN_TEXT_CHARS = int(os.getenv("PDF_MIN_TEXT_CHARS", "100"))
MAX_PDF_PAGES = 10

EXTRACTION_PROMPT = """You are a financial document parser. Extract ALL transactions from this bank statement or receipt.

Return ONLY valid JSON — no markdown, no explanation:
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
- If you cannot read the document clearly, return {"bank": null, "transactions": []}"""


def _extract_pdf_text(file_bytes: bytes) -> str:
    import fitz
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return "".join(page.get_text() for page in doc).strip()


def _pdf_to_images(file_bytes: bytes) -> list[bytes]:
    import fitz
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images = []
    for i, page in enumerate(doc):
        if i >= MAX_PDF_PAGES:
            logger.warning("PDF has >%d pages — truncating to first %d", MAX_PDF_PAGES, MAX_PDF_PAGES)
            break
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        images.append(pix.tobytes("png"))
    return images


def _parse_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def _call_text(text: str) -> dict:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": f"{EXTRACTION_PROMPT}\n\n{text}"}],
        temperature=0,
    )
    return _parse_response(response.choices[0].message.content)


def _call_vision(image_bytes_list: list[bytes], mime_type: str = "image/png") -> dict:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    content = [{"type": "text", "text": EXTRACTION_PROMPT}]
    for img in image_bytes_list:
        b64 = base64.b64encode(img).decode()
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{b64}"},
        })
    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{"role": "user", "content": content}],
        temperature=0,
    )
    return _parse_response(response.choices[0].message.content)


def extract_from_bytes(
    file_bytes: bytes,
    filename: str,
    mime_type: str,
) -> ExtractionResult:
    if not GROQ_API_KEY:
        logger.info("GROQ_API_KEY not set — extraction disabled (test mode)")
        return ExtractionResult(
            transactions=[],
            source_file=filename,
            bank_detected=None,
            extraction_notes="Extraction disabled: GROQ_API_KEY not configured",
        )

    try:
        if mime_type == "application/pdf":
            text = _extract_pdf_text(file_bytes)
            if len(text) >= MIN_TEXT_CHARS:
                logger.info("Text PDF detected (%d chars) — using text model", len(text))
                data = _call_text(text)
            else:
                logger.info("Scanned PDF detected — converting to images")
                images = _pdf_to_images(file_bytes)
                if not images:
                    return ExtractionResult(
                        transactions=[],
                        source_file=filename,
                        bank_detected=None,
                        extraction_notes="Extraction error: could not render PDF pages",
                    )
                data = _call_vision(images)
        else:
            data = _call_vision([file_bytes], mime_type)

    except json.JSONDecodeError as e:
        logger.error("Groq returned invalid JSON: %s", e)
        return ExtractionResult(
            transactions=[],
            source_file=filename,
            bank_detected=None,
            extraction_notes=f"Extraction error: {e}",
        )
    except Exception as e:
        logger.error("Groq extraction failed: %s", e)
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
