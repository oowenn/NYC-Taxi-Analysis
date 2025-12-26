"""
Circuit breaker middleware
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from collections import deque
from datetime import datetime, timedelta
import time


class CircuitBreaker:
    def __init__(self, error_threshold: int = 10, time_window: int = 60, disable_threshold: int = 100):
        self.error_threshold = error_threshold
        self.time_window = time_window
        self.disable_threshold = disable_threshold
        self.errors = deque()
        self.requests = deque()
        self.is_open_flag = False
    
    def record_error(self):
        """Record an error"""
        self.errors.append(time.time())
        self._clean_old_errors()
        
        if len(self.errors) >= self.error_threshold:
            self.is_open_flag = True
    
    def record_request(self):
        """Record a request"""
        self.requests.append(time.time())
        self._clean_old_requests()
        
        if len(self.requests) >= self.disable_threshold:
            self.is_open_flag = True
    
    def _clean_old_errors(self):
        """Remove errors older than time window"""
        now = time.time()
        while self.errors and now - self.errors[0] > self.time_window:
            self.errors.popleft()
    
    def _clean_old_requests(self):
        """Remove requests older than time window"""
        now = time.time()
        while self.requests and now - self.requests[0] > self.time_window:
            self.requests.popleft()
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        self._clean_old_errors()
        self._clean_old_requests()
        
        # Auto-close if errors cleared
        if len(self.errors) < self.error_threshold // 2:
            self.is_open_flag = False
        
        return self.is_open_flag
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.errors.clear()
        self.requests.clear()
        self.is_open_flag = False


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        circuit_breaker = request.app.state.circuit_breaker
        
        if request.url.path == "/api/chat":
            circuit_breaker.record_request()
        
        try:
            response = await call_next(request)
            
            if response.status_code >= 500:
                circuit_breaker.record_error()
            
            return response
        except Exception as e:
            circuit_breaker.record_error()
            raise

