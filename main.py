
import base64
import time
import uuid
import threading
from collections import deque

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

TOTAL_ORDERS = 50
RATE_LIMIT = 18
WINDOW_SECONDS = 10

# In-memory state for a single running instance.
idempotency_store = {}
orders_lock = threading.Lock()
rate_buckets = {}
rate_lock = threading.Lock()


class OrderRequest(BaseModel):
    product: str = "standard"
    quantity: int = 1


class RateLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] == "OPTIONS":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        client_id = headers.get(
            b"x-client-id", b""
        ).decode().strip()

        if not client_id:
            client = scope.get("client")
            client_id = client[0] if client else "unknown"

        now = time.monotonic()

        with rate_lock:
            bucket = rate_buckets.setdefault(client_id, deque())

            # Remove requests outside the rolling time window.
            while bucket and now - bucket[0] >= WINDOW_SECONDS:
                bucket.popleft()

            if len(bucket) >= RATE_LIMIT:
                retry_after = max(
                    1,
                    int(WINDOW_SECONDS - (now - bucket[0]) + 0.999),
                )

                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={
                        "Retry-After": str(retry_after),
                    },
                )

                await response(scope, receive, send)
                return

            bucket.append(now)

        await self.app(scope, receive, send)


app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/orders", status_code=201)
def create_order(
    body: OrderRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    with orders_lock:
        if idempotency_key in idempotency_store:
            return idempotency_store[idempotency_key]

        order = {
            "id": str(uuid.uuid4()),
            "product": body.product,
            "quantity": body.quantity,
        }

        idempotency_store[idempotency_key] = order
        return order


@app.get("/orders")
def list_orders(limit: int = 10, cursor: str | None = None):
    if limit < 1:
        raise HTTPException(
            status_code=422,
            detail="limit must be positive",
        )

    offset = 0

    if cursor:
        try:
            offset = int(
                base64.urlsafe_b64decode(cursor.encode()).decode()
            )
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid cursor",
            )

    if offset < 0 or offset > TOTAL_ORDERS:
        raise HTTPException(
            status_code=400,
            detail="Invalid cursor",
        )

    end = min(offset + limit, TOTAL_ORDERS)

    items = [
        {"id": i, "status": "available"}
        for i in range(offset + 1, end + 1)
    ]

    next_cursor = (
        base64.urlsafe_b64encode(str(end).encode()).decode()
        if end < TOTAL_ORDERS
        else None
    )

    return {
        "items": items,
        "next_cursor": next_cursor,
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok"}

import base64
import time
import uuid
import threading
from collections import deque

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

TOTAL_ORDERS = 50
RATE_LIMIT = 18
WINDOW_SECONDS = 10

# In-memory state for a single running instance.
idempotency_store = {}
orders_lock = threading.Lock()
rate_buckets = {}
rate_lock = threading.Lock()


class OrderRequest(BaseModel):
    product: str = "standard"
    quantity: int = 1


class RateLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] == "OPTIONS":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        client_id = headers.get(
            b"x-client-id", b""
        ).decode().strip()

        if not client_id:
            client = scope.get("client")
            client_id = client[0] if client else "unknown"

        now = time.monotonic()

        with rate_lock:
            bucket = rate_buckets.setdefault(client_id, deque())

            # Remove requests outside the rolling time window.
            while bucket and now - bucket[0] >= WINDOW_SECONDS:
                bucket.popleft()

            if len(bucket) >= RATE_LIMIT:
                retry_after = max(
                    1,
                    int(WINDOW_SECONDS - (now - bucket[0]) + 0.999),
                )

                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={
                        "Retry-After": str(retry_after),
                    },
                )

                await response(scope, receive, send)
                return

            bucket.append(now)

        await self.app(scope, receive, send)


app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/orders", status_code=201)
def create_order(
    body: OrderRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
):
    with orders_lock:
        if idempotency_key in idempotency_store:
            return idempotency_store[idempotency_key]

        order = {
            "id": str(uuid.uuid4()),
            "product": body.product,
            "quantity": body.quantity,
        }

        idempotency_store[idempotency_key] = order
        return order


@app.get("/orders")
def list_orders(limit: int = 10, cursor: str | None = None):
    if limit < 1:
        raise HTTPException(
            status_code=422,
            detail="limit must be positive",
        )

    offset = 0

    if cursor:
        try:
            offset = int(
                base64.urlsafe_b64decode(cursor.encode()).decode()
            )
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid cursor",
            )

    if offset < 0 or offset > TOTAL_ORDERS:
        raise HTTPException(
            status_code=400,
            detail="Invalid cursor",
        )

    end = min(offset + limit, TOTAL_ORDERS)

    items = [
        {"id": i, "status": "available"}
        for i in range(offset + 1, end + 1)
    ]

    next_cursor = (
        base64.urlsafe_b64encode(str(end).encode()).decode()
        if end < TOTAL_ORDERS
        else None
    )

    return {
        "items": items,
        "next_cursor": next_cursor,
    }


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
