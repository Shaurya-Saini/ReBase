"""CONTRACT §1 error format: {"error": {"code": "SNAKE_UPPER", "message": "..."}}."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, **extra: Any):
        self.status = status
        self.code = code
        self.message = message
        self.extra = extra  # e.g. items=["chk_02"] for CRITICAL_DEFECT


def _body(code: str, message: str, **extra: Any) -> dict:
    return {"error": {"code": code, "message": message, **extra}}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError):
        return JSONResponse(_body(exc.code, exc.message, **exc.extra), status_code=exc.status)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(_body(code, str(exc.detail)), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        return JSONResponse(
            _body("VALIDATION_ERROR", "Invalid request", details=jsonable(exc.errors())),
            status_code=422,
        )


def jsonable(errors: list) -> list:
    # Pydantic error dicts may hold non-JSON values (e.g. exceptions in ctx).
    return [{k: v for k, v in e.items() if k in ("loc", "msg", "type")} for e in errors]
