"""FastAPI application entry point."""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import check_db_connection
from .schemas import HealthResponse
from .services.detector import FaceDetector, FaceDetectorUnavailableError
from .services.broadcaster import ConnectionManager
from .routers import ingest, stream, roi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
detector: FaceDetector = None
broadcaster: ConnectionManager = None
executor: ThreadPoolExecutor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global detector, broadcaster, executor
    
    logger.info("Starting application...")
    
    # Initialize face detector
    try:
        detector = FaceDetector(backend=settings.detector_backend)
        logger.info(f"Face detector initialized: {detector.backend}")
    except FaceDetectorUnavailableError as e:
        logger.error(f"Failed to initialize face detector: {e}")
        detector = None
    
    # Initialize broadcaster
    broadcaster = ConnectionManager(max_queue_size=settings.broadcast_queue_size)
    logger.info("Broadcaster initialized")
    
    # Initialize thread pool executor for blocking operations
    executor = ThreadPoolExecutor(max_workers=4)
    logger.info("Thread pool executor initialized")
    
    # Set global instances in routers
    ingest.set_detector(detector)
    ingest.set_broadcaster(broadcaster)
    ingest.set_executor(executor)
    stream.set_broadcaster(broadcaster)
    
    logger.info("Application startup complete")
    
    yield
    
    # Cleanup
    logger.info("Shutting down application...")
    
    if executor is not None:
        executor.shutdown(wait=True)
        logger.info("Thread pool executor shut down")
    
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Face Detection Video Streaming API",
    description="Real-time face detection and video streaming system",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router)
app.include_router(stream.router)
app.include_router(roi.router)


@app.get("/api/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        Health status including database and detector availability
    """
    # Check database connection
    db_healthy = await check_db_connection()
    
    # Check detector availability
    detector_healthy = detector is not None and detector.is_available()
    
    # Overall status
    overall_status = "healthy" if (db_healthy and detector_healthy) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        db=db_healthy,
        detector=detector_healthy
    )


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """Root endpoint."""
    return {
        "message": "Face Detection Video Streaming API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
