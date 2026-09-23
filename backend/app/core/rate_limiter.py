import time
from typing import Dict, Tuple
from fastapi import Request
from backend.app.core.config import settings
from backend.app.core.exceptions import RateLimitExceededError

class InMemoryRateLimiter:
    def __init__(self):
        # Key -> (tokens, last_refill_timestamp)
        self.buckets: Dict[str, Tuple[float, float]] = {}

    def is_allowed(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        now = time.time()
        fill_rate = max_requests / window_seconds

        if key not in self.buckets:
            self.buckets[key] = (max_requests - 1.0, now)
            return True

        tokens, last_refill = self.buckets[key]
        elapsed = now - last_refill
        refilled_tokens = min(float(max_requests), tokens + elapsed * fill_rate)

        if refilled_tokens >= 1.0:
            self.buckets[key] = (refilled_tokens - 1.0, now)
            return True
        else:
            self.buckets[key] = (refilled_tokens, now)
            return False

rate_limiter = InMemoryRateLimiter()

async def check_rate_limit(request: Request, limit_type: str = "unauth"):
    client_ip = request.client.host if request.client else "127.0.0.1"
    auth_header = request.headers.get("Authorization", "")
    path = request.url.path

    if "stream" in path or "messages" in path:
        limit = settings.RATE_LIMIT_AI
        key = f"rate:ai:{auth_header or client_ip}"
    elif auth_header:
        limit = settings.RATE_LIMIT_AUTH
        key = f"rate:auth:{auth_header}"
    else:
        limit = settings.RATE_LIMIT_UNAUTH
        key = f"rate:unauth:{client_ip}"

    # Verify limit
    allowed = rate_limiter.is_allowed(key, max_requests=limit, window_seconds=60)
    if not allowed:
        raise RateLimitExceededError(
            f"Rate limit exceeded ({limit} requests/minute). Please slow down.",
            code="RATE_LIMIT_EXCEEDED"
        )
