import logging
import sys
import json
import time
from typing import Any, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import uuid

# Define custom JSON Formatter
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        if hasattr(record, "organization_id"):
            log_obj["organization_id"] = record.organization_id
        if hasattr(record, "extra_data"):
            log_obj["data"] = record.extra_data
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging():
    logger = logging.getLogger("supportiq")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.error").handlers = []
    
    return logger

logger = setup_logging()

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        start_time = time.time()

        # Call the next middleware or router
        try:
            response = await call_next(request)
            latency = (time.time() - start_time) * 1000
            response.headers["X-Request-ID"] = request_id

            # Exclude health checks from noisy logs
            if not request.url.path.startswith("/health") and not request.url.path.startswith("/ready"):
                logger.info(
                    f"{request.method} {request.url.path} - {response.status_code} ({latency:.2f}ms)",
                    extra={"extra_data": {
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "latency_ms": round(latency, 2),
                        "client_ip": request.client.host if request.client else "unknown"
                    }}
                )
            return response
        except Exception as exc:
            latency = (time.time() - start_time) * 1000
            logger.error(
                f"Unhandled Exception: {request.method} {request.url.path} ({latency:.2f}ms): {str(exc)}",
                exc_info=True,
                extra={"extra_data": {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "latency_ms": round(latency, 2)
                }}
            )
            raise exc
