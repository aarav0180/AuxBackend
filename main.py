"""
VibeSync Backend - Collaborative Music Streaming Application

A FastAPI backend for synchronized music listening rooms.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.core.config import settings
from src.core.exceptions import VibesyncException
from src.core.encryption import encrypt_response
from src.api.rooms import router as rooms_router
from src.api.search import router as search_router
from src.services.jiosaavn_service import jiosaavn_service
from src.services.room_manager import room_manager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ==================== Encryption Middleware ====================

class ResponseEncryptionMiddleware(BaseHTTPMiddleware):
    """Middleware to encrypt all JSON responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Intercept response and encrypt if JSON."""
        response = await call_next(request)
        
        # Only encrypt JSON responses (not docs, static files, etc.)
        if (
            response.status_code == 200 and
            response.headers.get("content-type", "").startswith("application/json") and
            not request.url.path.startswith("/docs") and
            not request.url.path.startswith("/redoc") and
            not request.url.path.startswith("/openapi.json")
        ):
            # Read the original response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            try:
                # Parse JSON and encrypt
                import json
                original_data = json.loads(body.decode())
                encrypted_data = encrypt_response(original_data)
                encrypted_json = json.dumps(encrypted_data)
                encrypted_bytes = encrypted_json.encode('utf-8')
                
                # Create new headers without Content-Length (it will be auto-calculated)
                new_headers = {k: v for k, v in response.headers.items() if k.lower() != 'content-length'}
                
                # Return encrypted response with correct content length
                return Response(
                    content=encrypted_bytes,
                    status_code=response.status_code,
                    headers=new_headers,
                    media_type="application/json"
                )
            except Exception as e:
                # If encryption fails, return original response
                logger.error(f"Encryption failed: {e}")
                new_headers = {k: v for k, v in response.headers.items() if k.lower() != 'content-length'}
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=new_headers,
                    media_type="application/json"
                )
        
        return response


# ==================== Lifespan Management ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    # Startup
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📡 JioSaavn API: {settings.JIOSAAVN_API_BASE_URL}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    await jiosaavn_service.close()
    logger.info("✅ Cleanup complete")


# ==================== App Initialization ====================

app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## VibeSync - Listen Together, Anywhere 🎵
    
    A collaborative music streaming backend that enables synchronized listening experiences.
    
    ### Features:
    - **Room Management**: Create and manage listening rooms
    - **Queue System**: Add and manage songs in a shared queue
    - **Sync Playback**: Keep all listeners in sync with the host
    - **JioSaavn Integration**: Search and play millions of songs
    
    ### How Sync Works:
    1. Host starts a room and adds songs
    2. Listeners join with the room code
    3. All clients poll `/rooms/{room_code}/sync` to get current playback state
    4. Frontend calculates: `seek_position = server_time - song_start_time`
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ==================== CORS Configuration ====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add encryption middleware
app.add_middleware(ResponseEncryptionMiddleware)


# ==================== Exception Handlers ====================

@app.exception_handler(VibesyncException)
async def vibesync_exception_handler(request: Request, exc: VibesyncException):
    """Handle custom VibeSync exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with user-friendly messages."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation failed",
            "details": errors,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(f"Unexpected error: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "An unexpected error occurred",
            "detail": str(exc) if settings.DEBUG else "Internal server error",
        },
    )


# ==================== Include Routers ====================

app.include_router(rooms_router)
app.include_router(search_router)


# ==================== Health & Info Endpoints ====================

@app.get(
    "/",
    tags=["Health"],
    summary="API Root",
    description="Welcome endpoint with API information.",
)
async def root():
    """Welcome endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    description="Check if the API is running and healthy.",
)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get(
    "/stats",
    tags=["Health"],
    summary="Server Stats",
    description="Get current server statistics.",
)
async def server_stats():
    """Get server statistics."""
    return {
        "active_rooms": room_manager.get_active_rooms_count(),
        "room_codes": room_manager.get_all_room_codes(),
    }


# ==================== Run Configuration ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
