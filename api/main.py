import logging
import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import auth, files, operations
from utils.errors import TSGError
from utils.logger import log_error, log_info
from utils.session_store import cleanup_expired_sessions

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="TSG API",
    description="API for Telegram Storage System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RATE_LIMIT = {
    "/auth": (5, 60),
    "/files": (30, 60),
}
_REQUEST_HISTORY: dict[tuple[str, str], deque[float]] = defaultdict(deque)
REQUEST_COUNT = 0
ERROR_COUNT = 0



def cleanup_rate_limit():
    now = time.time()
    keys_to_delete = []
    for key, history in _REQUEST_HISTORY.items():
        if not history or now - history[-1] > 300:
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del _REQUEST_HISTORY[key]


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    global REQUEST_COUNT
    REQUEST_COUNT += 1

    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    path = request.url.path
    now = time.time()
    if now % 100 < 1:
        cleanup_rate_limit()
    if now % 60 < 1:
        cleanup_expired_sessions(300)

    limit_rule = None
    matched_prefix = None
    for prefix, rule in RATE_LIMIT.items():
        if path.startswith(prefix):
            limit_rule = rule
            matched_prefix = prefix
            break

    if limit_rule:
        max_requests, window_seconds = limit_rule
        client_ip = request.client.host if request.client else "unknown"
        key = (client_ip, matched_prefix)

        history = _REQUEST_HISTORY[key]
        while history and now - history[0] > window_seconds:
            history.popleft()

        if len(history) >= max_requests:
            log_info("rate_limit_exceeded", request_id=request_id, path=path, retry_after=window_seconds)
            return JSONResponse(status_code=429, content={"error": "Rate limit exceeded", "retry_after": window_seconds})

        history.append(now)

    log_info("request_start", request_id=request_id, path=path)
    response = await call_next(request)
    log_info("request_end", request_id=request_id, path=path, status=response.status_code)
    return response


@app.exception_handler(TSGError)
async def tsg_error_handler(request: Request, exc: TSGError):
    global ERROR_COUNT
    ERROR_COUNT += 1
    log_error("tsg_error", error=str(exc), request_id=getattr(request.state, "request_id", None), path=request.url.path)
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    global ERROR_COUNT
    ERROR_COUNT += 1
    detail = exc.detail
    if isinstance(detail, dict) and "error" in detail:
        payload = detail
    else:
        payload = {"error": str(detail)}
    log_error("http_error", error=str(payload.get("error")), status=exc.status_code, request_id=getattr(request.state, "request_id", None), path=request.url.path)
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    global ERROR_COUNT
    ERROR_COUNT += 1
    first_error = exc.errors()[0].get("msg", "Validation error") if exc.errors() else "Validation error"
    log_error("validation_error", error=first_error, request_id=getattr(request.state, "request_id", None), path=request.url.path)
    return JSONResponse(status_code=422, content={"error": first_error})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    return {"requests": REQUEST_COUNT, "errors": ERROR_COUNT}


app.include_router(auth.router)
app.include_router(files.router)
app.include_router(operations.router)
