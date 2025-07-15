"""Main FastAPI application for KURE embedding API - Refactored with routers."""

import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from services import embedding_service
from services.qdrant_service import qdrant_service
from services.unified_search_service import unified_search_service

# Import routers
from routers.embeddings import router as embeddings_router
from routers.files import router as files_router
from routers.search import router as search_router
from routers.admin import router as admin_router
from routers.rerank import router as rerank_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting KURE API service...")
    start_time = time.time()

    try:
        # Load embedding model
        embedding_service.load_model(settings.default_model)

        # Initialize Qdrant (already done in service init, but verify connection)
        qdrant_health = qdrant_service.health_check()
        if qdrant_health.get("connected"):
            logger.info(f"✅ Qdrant connected: {qdrant_health.get('total_collections', 0)} collections")
        else:
            logger.warning(f"⚠️ Qdrant connection issue: {qdrant_health.get('error', 'Unknown')}")

        # Initialize unified search service
        logger.info("🔧 Initializing unified search service...")
        unified_init = await unified_search_service.initialize()
        if unified_init:
            logger.info("✅ Unified search service initialized successfully")
        else:
            logger.warning("⚠️ Unified search service initialization failed")

        # Initialize rerank service
        logger.info("🔧 Initializing rerank service...")
        try:
            from services.rerank_service import rerank_service
            rerank_init = await rerank_service.initialize()
            if rerank_init:
                logger.info("✅ Rerank service initialized successfully")
            else:
                logger.warning("⚠️ Rerank service initialization failed")
        except Exception as e:
            logger.warning(f"⚠️ Rerank service initialization failed: {e}")

        startup_time = time.time() - start_time
        logger.info(f"🚀 KURE API service started successfully in {startup_time:.2f} seconds")

    except Exception as e:
        logger.error(f"❌ Failed to start KURE API service: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down KURE API service...")
    try:
        # Clean up old uploaded files
        try:
            from services.file_upload_service import file_upload_service
            file_upload_service.cleanup_old_files(max_age_hours=24)
        except Exception as e:
            logger.warning(f"Error cleaning up files: {e}")

        # Clean up rerank service
        try:
            from services.rerank_service import rerank_service
            await rerank_service.cleanup()
        except Exception as e:
            logger.warning(f"Error cleaning up rerank service: {e}")

        # Clean up embedding service
        embedding_service.cleanup_memory()

        logger.info("✅ KURE API service shutdown completed")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title="KURE Embedding API",
    description="Korean Universal Representation Embedding API with document processing and search capabilities",
    version=settings.app_version,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "KURE Embedding API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


# Basic endpoints
@app.get("/ping")
async def ping():
    """Simple ping endpoint."""
    return {"message": "pong"}


# Include routers
app.include_router(embeddings_router, tags=["Embeddings"])
app.include_router(files_router, tags=["Files"])
app.include_router(search_router, tags=["Search"])
app.include_router(admin_router, tags=["Admin"])
app.include_router(rerank_router, tags=["Rerank"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=settings.log_level.lower()
    )
