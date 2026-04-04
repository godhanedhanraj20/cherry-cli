import logging
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.routes import auth, files, operations
from utils.errors import TSGError

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="TSG API",
    description="API for Telegram Storage System",
    version="1.0.0",
)

RATE_LIMIT = {
    "/auth": (5, 60),
    "/files": (30, 60),
}
_REQUEST_HISTORY: dict[tuple[str, str], deque[float]] = defaultdict(deque)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    limit_rule = None
    for prefix, rule in RATE_LIMIT.items():
        if path.startswith(prefix):
            limit_rule = rule
            break

    if limit_rule:
        max_requests, window_seconds = limit_rule
        client_ip = request.client.host if request.client else "unknown"
        key = (client_ip, prefix)
        now = time.time()

        history = _REQUEST_HISTORY[key]
        while history and now - history[0] > window_seconds:
            history.popleft()

        if len(history) >= max_requests:
            return JSONResponse(status_code=429, content={"error": "Rate limit exceeded"})

        history.append(now)

    return await call_next(request)


@app.exception_handler(TSGError)
async def tsg_error_handler(_, exc: TSGError):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        payload = detail
    else:
        payload = {"error": str(detail)}
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    first_error = exc.errors()[0].get("msg", "Validation error") if exc.errors() else "Validation error"
    return JSONResponse(status_code=422, content={"error": first_error})


app.include_router(auth.router)
app.include_router(files.router)
app.include_router(operations.router)
