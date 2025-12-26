"""
Quota and status endpoint
"""
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/quota")
async def get_quota(request: Request):
    """Get remaining quota and LLM status"""
    circuit_breaker = request.app.state.circuit_breaker
    client_ip = request.client.host if request.client else "unknown"
    
    # Get rate limit info from middleware
    from middleware.rate_limit import rate_limit_store, daily_global_count
    import time
    from datetime import datetime
    
    now = time.time()
    client_requests = rate_limit_store.get(client_ip, [])
    client_requests[:] = [req_time for req_time in client_requests if now - req_time < 86400]
    
    recent = [req_time for req_time in client_requests if now - req_time < 60]
    
    # Get limits from env
    import os
    per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "5"))
    per_day = int(os.getenv("RATE_LIMIT_PER_DAY", "50"))
    
    remaining = {
        "per_minute": max(0, per_minute - len(recent)),
        "per_day": max(0, per_day - len(client_requests))
    }
    
    return {
        "llm_enabled": not circuit_breaker.is_open(),
        "remaining_requests": remaining,
        "circuit_breaker_status": "open" if circuit_breaker.is_open() else "closed"
    }

