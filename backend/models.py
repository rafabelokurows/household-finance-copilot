from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Owner(str, Enum):
    Rafael = "Rafael"
    Heloisa = "Heloisa"
    Shared = "Shared"


class Status(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Currency(str, Enum):
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"
    BRL = "BRL"
    CHF = "CHF"
    PLN = "PLN"
    CZK = "CZK"


class Category(str, Enum):
    Groceries = "Groceries"
    Restaurants = "Restaurants"
    Transportation = "Transportation"
    Utilities = "Utilities"
    Shopping = "Shopping"
    Entertainment = "Entertainment"
    Healthcare = "Healthcare"
    Travel = "Travel"
    Insurance = "Insurance"
    Salary = "Salary"
    Bonus = "Bonus"
    Investments = "Investments"
    Other = "Other"


class TransactionBase(BaseModel):
    date: date
    merchant: str
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    currency: Currency = Currency.EUR
    category: Optional[Category] = None
    owner: Optional[Owner] = None
    bank: Optional[str] = None


class TransactionCreate(TransactionBase):
    confidence: float = Field(ge=0.0, le=1.0)
    source_file: Optional[str] = None
    raw_json: Optional[dict] = None


class TransactionUpdate(BaseModel):
    date: Optional[date] = None
    merchant: Optional[str] = None
    amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    currency: Optional[Currency] = None
    category: Optional[Category] = None
    owner: Optional[Owner] = None
    status: Optional[Status] = None
    bank: Optional[str] = None


class Transaction(TransactionBase):
    id: str
    confidence: float
    status: Status = Status.pending
    source_file: Optional[str] = None
    raw_json: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExtractedTransaction(BaseModel):
    date: Optional[str] = None
    merchant: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Currency = Currency.EUR
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    notes: Optional[str] = None


class ExtractionResult(BaseModel):
    transactions: list[ExtractedTransaction]
    source_file: str
    bank_detected: Optional[str] = None
    extraction_notes: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    transaction_id: str
    filename: str
    mime_type: str
    data: str  # base64-encoded file content
    uploaded_at: str
