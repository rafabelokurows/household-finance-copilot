import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TIMEOUT = 10
TOKEN_EXPIRATION_HOURS = 24
PAGE_SIZE = 10

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
    "transactions": f"{API_BASE_URL}/api/transactions",
    "transaction_tags": f"{API_BASE_URL}/api/transactions",
    "all_tags": f"{API_BASE_URL}/api/tags",
    "analytics_by_tag": f"{API_BASE_URL}/api/analytics/by_tag",
}

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
