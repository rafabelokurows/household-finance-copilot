import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.client import get_connection
from .ingestion.gmail_poller import start_polling
from .routers import upload, transactions, review, auth, analytics, documents, tags, categories

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_connection()       # initialise DB + schema
    start_polling()        # start Gmail background thread (no-op if no credentials)
    yield


app = FastAPI(title="Household Financial Copilot", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(upload.router, prefix="/api/upload", tags=["ingestion"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(review.router, prefix="/api/review", tags=["review"])
app.include_router(documents.router, prefix="/api/transactions", tags=["documents"])
app.include_router(tags.router, prefix="/api", tags=["tags"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])


@app.get("/health")
def health():
    return {"status": "ok"}
