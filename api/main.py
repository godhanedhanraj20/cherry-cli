from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.routes import auth, files, operations
from utils.errors import TSGError

app = FastAPI(
    title="TSG API",
    description="API for Telegram Storage System",
    version="1.0.0",
)


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
