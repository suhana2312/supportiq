from typing import Optional, Any, Dict
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

class BaseAppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Any] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)

class AuthenticationError(BaseAppException):
    def __init__(self, message: str = "Authentication failed", code: str = "AUTHENTICATION_FAILED"):
        super().__init__(code=code, message=message, status_code=status.HTTP_401_UNAUTHORIZED)

class PermissionDeniedError(BaseAppException):
    def __init__(self, message: str = "Permission denied", code: str = "PERMISSION_DENIED"):
        super().__init__(code=code, message=message, status_code=status.HTTP_403_FORBIDDEN)

class NotFoundError(BaseAppException):
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(code=code, message=message, status_code=status.HTTP_404_NOT_FOUND)

class TenantIsolationError(BaseAppException):
    def __init__(self, message: str = "Cross-tenant access forbidden", code: str = "TENANT_ACCESS_DENIED"):
        super().__init__(code=code, message=message, status_code=status.HTTP_403_FORBIDDEN)

class BusinessRuleViolationError(BaseAppException):
    def __init__(self, message: str, code: str = "BUSINESS_RULE_VIOLATION"):
        super().__init__(code=code, message=message, status_code=status.HTTP_400_BAD_REQUEST)

class RateLimitExceededError(BaseAppException):
    def __init__(self, message: str = "Rate limit exceeded. Please slow down.", code: str = "RATE_LIMIT_EXCEEDED"):
        super().__init__(code=code, message=message, status_code=status.HTTP_429_TOO_MANY_REQUESTS)

class DocumentProcessingError(BaseAppException):
    def __init__(self, message: str, code: str = "DOCUMENT_PROCESSING_FAILED"):
        super().__init__(code=code, message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


def register_exception_handlers(app):
    @app.exception_handler(BaseAppException)
    async def app_exception_handler(request: Request, exc: BaseAppException):
        payload: Dict[str, Any] = {
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
        if exc.details is not None:
            payload["error"]["details"] = exc.details
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        first_error = exc.errors()[0] if exc.errors() else {}
        loc = " -> ".join([str(l) for l in first_error.get("loc", []) if l != "body"])
        msg = first_error.get("msg", "Validation error")
        formatted_message = f"Field validation failed on '{loc}': {msg}" if loc else msg
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": formatted_message,
                    "details": exc.errors()
                }
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(exc.detail)
                }
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # Prevent stack trace leakage in responses
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred. Please try again later."
                }
            }
        )
