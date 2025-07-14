"""Administrative and monitoring API routes."""

import logging
from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional

from models import (
    MonitoringStatsResponse,
    QdrantStatsResponse,
    StorageStatsResponse, StorageFilesResponse, StorageCleanupResponse,
    DuplicateStatsResponse, DuplicateListResponse,
    DataConsistencyResponse, DataRepairResponse,
    ChunkRequest, ChunkResponse, ChunkData,
    RerankRequest, RerankResponse, RerankResult
)
from services import chunking_service
from services.database_service import database_service
from services.qdrant_service import qdrant_service
from services.storage_service import storage_service
from services.rerank_service import rerank_service
from routers.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")


# Monitoring endpoints
@router.get("/monitoring/stats", response_model=MonitoringStatsResponse)
async def get_monitoring_stats(
    authorization: str = Depends(verify_api_key)
):
    """Get basic monitoring statistics."""
    try:
        from services.monitoring_service import monitoring_service

        stats = monitoring_service.get_basic_stats()
        return MonitoringStatsResponse(
            success=True,
            **stats
        )
    except Exception as e:
        logger.error(f"Error getting monitoring stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring stats: {str(e)}"
        )


# Qdrant management endpoints
@router.get("/qdrant/stats", response_model=QdrantStatsResponse)
async def get_qdrant_stats(authorization: str = Depends(verify_api_key)):
    """Get Qdrant collection statistics."""
    try:
        stats = qdrant_service.get_collection_stats()
        return QdrantStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting Qdrant stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Qdrant stats: {str(e)}"
        )


@router.get("/qdrant/health")
async def get_qdrant_health(authorization: str = Depends(verify_api_key)):
    """Check Qdrant service health."""
    try:
        health = qdrant_service.health_check()
        return health
    except Exception as e:
        logger.error(f"Error checking Qdrant health: {str(e)}")
        return {
            "status": "error",
            "connected": False,
            "error": str(e)
        }


# Storage management endpoints
@router.get("/storage/stats", response_model=StorageStatsResponse)
async def get_storage_stats(authorization: str = Depends(verify_api_key)):
    """Get storage usage statistics."""
    try:
        stats = storage_service.get_storage_stats()
        return StorageStatsResponse(
            success=True,
            stats=stats
        )
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage stats: {str(e)}"
        )


@router.get("/storage/files/{directory_type}", response_model=StorageFilesResponse)
async def list_storage_files(
    directory_type: str,
    file_type: Optional[str] = None,
    authorization: str = Depends(verify_api_key)
):
    """List files in storage directory."""
    try:
        if directory_type not in ["uploads", "processed", "temp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid directory type. Must be 'uploads', 'processed', or 'temp'"
            )

        files = storage_service.list_files(directory_type, file_type)
        return {
            "success": True,
            "directory_type": directory_type,
            "file_type": file_type,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        logger.error(f"Error listing storage files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list storage files: {str(e)}"
        )


@router.post("/storage/cleanup", response_model=StorageCleanupResponse)
async def cleanup_storage(
    days_old: int = 30,
    authorization: str = Depends(verify_api_key)
):
    """Clean up old files from storage."""
    try:
        if days_old < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="days_old must be >= 1"
            )

        result = storage_service.cleanup_old_files(days_old)
        return StorageCleanupResponse(**result)
    except Exception as e:
        logger.error(f"Error cleaning up storage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage cleanup failed: {str(e)}"
        )


# Duplicate management endpoints
@router.get("/duplicates/stats", response_model=DuplicateStatsResponse)
async def get_duplicate_stats(authorization: str = Depends(verify_api_key)):
    """Get duplicate file statistics."""
    try:
        stats = database_service.get_duplicate_stats()
        return DuplicateStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting duplicate stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get duplicate stats: {str(e)}"
        )


@router.get("/duplicates/list", response_model=DuplicateListResponse)
async def list_duplicates(
    page: int = 1,
    page_size: int = 50,
    authorization: str = Depends(verify_api_key)
):
    """List duplicate files."""
    try:
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be >= 1"
            )

        if page_size < 1 or page_size > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 500"
            )

        result = database_service.list_duplicates(page=page, page_size=page_size)
        return DuplicateListResponse(**result)
    except Exception as e:
        logger.error(f"Error listing duplicates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list duplicates: {str(e)}"
        )


# Data consistency endpoints
@router.get("/data/consistency", response_model=DataConsistencyResponse)
async def check_data_consistency(authorization: str = Depends(verify_api_key)):
    """Check data consistency between database and vector store."""
    try:
        result = database_service.check_data_consistency()
        return DataConsistencyResponse(**result)
    except Exception as e:
        logger.error(f"Error checking data consistency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data consistency check failed: {str(e)}"
        )


@router.post("/data/repair", response_model=DataRepairResponse)
async def repair_data_inconsistencies(
    dry_run: bool = True,
    authorization: str = Depends(verify_api_key)
):
    """Repair data inconsistencies between database and vector store."""
    try:
        result = database_service.repair_data_inconsistencies(dry_run=dry_run)
        return DataRepairResponse(**result)
    except Exception as e:
        logger.error(f"Error repairing data inconsistencies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data repair failed: {str(e)}"
        )


# Chunking endpoint
@router.post("/chunk", response_model=ChunkResponse)
async def chunk_text(
    request: ChunkRequest,
    authorization: str = Depends(verify_api_key)
):
    """Split text into chunks using various strategies."""
    try:
        chunks = chunking_service.chunk_text(
            text=request.text,
            strategy=request.strategy,
            chunk_size=request.chunk_size,
            overlap=request.overlap,
            separators=request.separators
        )

        chunk_data = [
            ChunkData(
                text=chunk,
                index=i,
                start_char=0,  # Would need to calculate actual positions
                end_char=len(chunk)
            )
            for i, chunk in enumerate(chunks)
        ]

        return ChunkResponse(
            chunks=chunk_data,
            total_chunks=len(chunks),
            strategy=request.strategy,
            chunk_size=request.chunk_size,
            overlap=request.overlap
        )

    except Exception as e:
        logger.error(f"Error chunking text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text chunking failed: {str(e)}"
        )
