"""
Rate limiting middleware
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict
import time

# In-memory rate limit storage (use Redis in production)
rate_limit_store = defaultdict(list)
daily_global_count = {"count": 0, "date": datetime.now().date()}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, per_minute: int = 5, per_day: int = 50, global_cap: int = 1000):
        super().__init__(app)
        self.per_minute = per_minute
        self.per_day = per_day
        self.global_cap = global_cap
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health endpoint
        if request.url.path == "/api/health":
            return await call_next(request)
        
        # Only rate limit /api/chat
        if request.url.path == "/api/chat":
            client_ip = request.client.host
            
            # Check global daily cap
            today = datetime.now().date()
            if daily_global_count["date"] != today:
                daily_global_count["count"] = 0
                daily_global_count["date"] = today
            
            if daily_global_count["count"] >= self.global_cap:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Global daily request limit exceeded"}
                )
            
            # Check per-IP limits
            now = time.time()
            client_requests = rate_limit_store[client_ip]
            
            # Clean old requests (older than 1 day)
            client_requests[:] = [req_time for req_time in client_requests if now - req_time < 86400]
            
            # Check per-minute limit
            recent_requests = [req_time for req_time in client_requests if now - req_time < 60]
            if len(recent_requests) >= self.per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"error": f"Rate limit exceeded: {self.per_minute} requests per minute"}
                )
            
            # Check per-day limit
            if len(client_requests) >= self.per_day:
                return JSONResponse(
                    status_code=429,
                    content={"error": f"Rate limit exceeded: {self.per_day} requests per day"}
                )
            
            # Record request
            client_requests.append(now)
            daily_global_count["count"] += 1
        
        return await call_next(request)
    
    def get_remaining(self, client_ip: str) -> Dict[str, int]:
        """Get remaining quota for an IP"""
        now = time.time()
        client_requests = rate_limit_store.get(client_ip, [])
        client_requests[:] = [req_time for req_time in client_requests if now - req_time < 86400]
        
        recent = [req_time for req_time in client_requests if now - req_time < 60]
        
        return {
            "per_minute": max(0, self.per_minute - len(recent)),
            "per_day": max(0, self.per_day - len(client_requests))
        }

