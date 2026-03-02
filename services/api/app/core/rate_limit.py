from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.errors import AppError


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, *, key: str, limit: int, window_seconds: int) -> None:
        now = time.time()
        with self._lock:
            bucket = self._buckets[key]
            while bucket and (now - bucket[0]) >= window_seconds:
                bucket.popleft()
            if len(bucket) >= limit:
                raise AppError(
                    code="TOO_MANY_REQUESTS",
                    message="rate limit exceeded",
                    http_status=429,
                )
            bucket.append(now)


rate_limiter = InMemoryRateLimiter()


def build_rate_limit_guard(*, action: str, limit: int, window_seconds: int):
    def guard(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        rate_limiter.check(
            key=f"{action}:{ip}",
            limit=limit,
            window_seconds=window_seconds,
        )

    return guard
