"""Mock rate limiter for Epic 2 testing."""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List

from fastapi import HTTPException, Request, Response, status


class InMemoryRateLimiter:
    """Mock rate limiter using API key tracking."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)

    async def check_rate_limit(self, request: Request) -> str:
        """Check if request is within rate limit.

        Args:
            request: FastAPI Request object

        Returns:
            API key if valid

        Raises:
            HTTPException: If API key is missing, invalid, or rate limit exceeded
        """
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "MISSING_API_KEY", "message": "API key required"}},
            )

        # Mock validation: accept any non-empty API key with minimum length
        if len(api_key) < 5:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "INVALID_API_KEY", "message": "Invalid API key"}},
            )

        # Check rate limit
        now = time.time()
        cutoff = now - self.window_seconds

        # Remove expired timestamps
        self.requests[api_key] = [t for t in self.requests[api_key] if t > cutoff]

        # Check if limit exceeded
        remaining = self.max_requests - len(self.requests[api_key])
        reset_time = int(now + self.window_seconds)

        if len(self.requests[api_key]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Maximum {self.max_requests} requests per minute per API key",
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                },
            )

        # Record this request
        self.requests[api_key].append(now)
        remaining -= 1

        # Store rate limit info for response headers (via request.state)
        request.state.rate_limit_info = {
            "limit": self.max_requests,
            "remaining": remaining,
            "reset": reset_time,
        }

        return api_key


def add_rate_limit_headers(response: Response, request: Request) -> Response:
    """Add rate limit headers to response.

    Args:
        response: FastAPI Response object
        request: FastAPI Request object with rate_limit_info in state

    Returns:
        Response with rate limit headers added
    """
    if hasattr(request.state, "rate_limit_info"):
        info = request.state.rate_limit_info
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])

    return response
