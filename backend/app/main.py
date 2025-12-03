import time
import uuid
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.routers import claims, auth, users, admin
from app.core.logging_config import (
    setup_logging,
    get_logger,
    set_correlation_id,
    clear_correlation_id,
    get_correlation_id
)

# Initialize logging on module load
setup_logging(level="INFO", json_format=True)

logger = get_logger(__name__)

app = FastAPI(
    title="Cloud-Native Insurance API",
    version="1.0.0"
)

logger.info(
    "Application initialized",
    extra={
        "event": "app_startup",
        "app_title": "Cloud-Native Insurance API",
        "app_version": "1.0.0"
    }
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next) -> Response:
    """
    Middleware for comprehensive request/response logging with correlation ID tracking.
    
    This middleware:
    1. Generates or extracts correlation ID for request tracing
    2. Logs incoming request details
    3. Tracks request duration
    4. Logs response status and any errors
    5. Adds correlation ID to response headers for client-side tracing
    """
    # Generate or extract correlation ID
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    set_correlation_id(correlation_id)
    
    # Extract request metadata
    request_id = str(uuid.uuid4())[:8]
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")
    
    # Log incoming request
    logger.info(
        f"Incoming request: {request.method} {request.url.path}",
        extra={
            "event": "request_started",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params) if request.query_params else None,
            "client_ip": client_ip,
            "user_agent": user_agent,
        }
    )
    
    # Track timing
    start_time = time.perf_counter()
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = logger.error
            status_category = "server_error"
        elif response.status_code >= 400:
            log_level = logger.warning
            status_category = "client_error"
        else:
            log_level = logger.info
            status_category = "success"
        
        # Log response
        log_level(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "event": "request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "status_category": status_category,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
            }
        )
        
        # Add correlation ID to response headers for client-side tracing
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-Duration-Ms"] = str(round(duration_ms, 2))
        
        return response
        
    except Exception as e:
        # Calculate duration even on error
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        logger.error(
            f"Request failed with exception: {request.method} {request.url.path}",
            extra={
                "event": "request_failed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration_ms, 2),
                "error_type": type(e).__name__,
                "error_message": str(e),
                "client_ip": client_ip,
            },
            exc_info=True
        )
        raise
    finally:
        # Clear correlation ID after request processing
        clear_correlation_id()


# --- ADD CORS MIDDLEWARE HERE ---
# This allows the frontend to talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (Safe for Dev, restrict in Prod)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include the router
app.include_router(claims.router, prefix="/api/v1/claims", tags=["Claims"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

logger.info(
    "All routers registered",
    extra={
        "event": "routers_registered",
        "routers": ["claims", "auth", "users", "admin"]
    }
)


@app.get("/")
def health_check():
    logger.debug(
        "Health check endpoint called",
        extra={"event": "health_check"}
    )
    return {"status": "healthy", "service": "insurance-backend"}


@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info(
        "Application startup complete - ready to accept requests",
        extra={
            "event": "startup_complete",
            "endpoints": [
                "/api/v1/claims",
                "/api/v1/auth",
                "/api/v1/users",
                "/api/v1/admin"
            ]
        }
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info(
        "Application shutting down",
        extra={"event": "shutdown"}
    )
