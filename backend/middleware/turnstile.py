"""
Cloudflare Turnstile verification middleware
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import httpx
import os
import json


class TurnstileMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip Turnstile for health and quota endpoints
        if request.url.path in ["/api/health", "/api/quota"]:
            return await call_next(request)
        
        # Only verify on /api/chat
        if request.url.path == "/api/chat":
            if request.method == "POST":
                # Check if we should skip verification (debug mode or demo key)
                secret_key = os.getenv("TURNSTILE_SECRET_KEY")
                debug_mode = os.getenv("DEBUG", "false").lower() == "true"
                demo_key = "1x00000000000000000000AA"
                
                if debug_mode or (secret_key == demo_key):
                    # Skip verification in local dev
                    print("⚠️  Turnstile verification skipped (debug mode or demo key)")
                    return await call_next(request)
                
                # Otherwise, verify the token
                try:
                    # Read body once and store it for the endpoint
                    body_bytes = await request.body()
                    if not body_bytes:
                        return JSONResponse(
                            status_code=400,
                            content={"error": "Request body required"}
                        )
                    
                    body = json.loads(body_bytes)
                    token = body.get("turnstile_token")
                    
                    if not token:
                        return JSONResponse(
                            status_code=400,
                            content={"error": "Turnstile token required"}
                        )
                    
                    # Verify token with Cloudflare
                    if secret_key:
                        async with httpx.AsyncClient() as client:
                            response = await client.post(
                                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                                data={
                                    "secret": secret_key,
                                    "response": token,
                                    "remoteip": request.client.host
                                }
                            )
                            result = response.json()
                            
                            if not result.get("success"):
                                return JSONResponse(
                                    status_code=403,
                                    content={"error": "Turnstile verification failed"}
                                )
                    
                    # Recreate request with body for FastAPI to parse
                    async def receive():
                        return {"type": "http.request", "body": body_bytes}
                    request._receive = receive
                    
                except Exception as e:
                    return JSONResponse(
                        status_code=400,
                        content={"error": f"Turnstile verification error: {str(e)}"}
                    )
        
        return await call_next(request)

