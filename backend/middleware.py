"""
Security middleware for FastAPI application
"""
import time
import uuid
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import redis
from config import settings
import logging

logger = logging.getLogger(__name__)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# Redis connection for rate limiting
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Rate limiting will use in-memory storage.")
    redis_client = None


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS header for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for audit purposes"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Get client info
        client_ip = get_remote_address(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"[{request_id}] from {client_ip}"
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = int((time.time() - start_time) * 1000)
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"[{request_id}] {response.status_code} in {duration}ms"
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"[{request_id}] {str(e)} in {duration}ms"
            )
            raise


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP whitelist middleware for admin endpoints"""
    
    def __init__(self, app, admin_ips: Optional[list] = None):
        super().__init__(app)
        self.admin_ips = admin_ips or []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this is an admin endpoint
        if request.url.path.startswith("/admin/"):
            client_ip = get_remote_address(request)
            
            # Allow localhost in development
            if settings.environment == "development" and client_ip in ["127.0.0.1", "::1"]:
                return await call_next(request)
            
            # Check whitelist
            if self.admin_ips and client_ip not in self.admin_ips:
                logger.warning(f"Unauthorized admin access attempt from {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
        
        return await call_next(request)


def setup_cors_middleware(app):
    """Setup CORS middleware"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"]
    )


def setup_rate_limiting(app):
    """Setup rate limiting middleware"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)


def setup_security_middleware(app, admin_ips: Optional[list] = None):
    """Setup all security middleware"""
    
    # Rate limiting
    setup_rate_limiting(app)
    
    # CORS
    setup_cors_middleware(app)
    
    # Custom security middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    
    # IP whitelist for admin endpoints
    if admin_ips:
        app.add_middleware(IPWhitelistMiddleware, admin_ips=admin_ips)


# Rate limiting decorators
def rate_limit_by_ip(rate: str = f"{settings.rate_limit_per_minute}/minute"):
    """Rate limit by IP address"""
    return limiter.limit(rate)


def rate_limit_by_user(rate: str = "100/minute"):
    """Rate limit by authenticated user"""
    def get_user_id(request: Request):
        # Extract user ID from JWT token if available
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            from services.auth import AuthService
            token = auth_header.split(" ")[1]
            token_data = AuthService.verify_token(token)
            if token_data:
                return str(token_data.user_id)
        return get_remote_address(request)
    
    return limiter.limit(rate, key_func=get_user_id)


# Webhook signature verification
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature using HMAC-SHA256"""
    import hmac
    import hashlib
    
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures securely
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

