"""Administrative API routes."""

import logging
from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional

from models import (
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
from config import settings
from services.unified_search_service import unified_search_service
from routers.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")




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


# Collection Management endpoints
@router.get("/admin/collections/status")
async def get_collections_status(authorization: str = Depends(verify_api_key)):
    """Get status of all collections (Qdrant and MeiliSearch)."""
    try:
        # Get Qdrant status
        qdrant_health = qdrant_service.health_check()
        qdrant_stats = qdrant_service.get_collection_stats()

        # Get MeiliSearch status
        meilisearch_health = {"status": "unknown", "backend": "meilisearch"}
        meilisearch_stats = {}

        try:
            # Try to get MeiliSearch backend directly
            if hasattr(unified_search_service, 'text_backend') and unified_search_service.text_backend:
                text_backend = unified_search_service.text_backend
                meilisearch_health = await text_backend.health_check()
                meilisearch_stats = text_backend.get_stats()
        except Exception as e:
            logger.warning(f"Could not get MeiliSearch status: {e}")
            meilisearch_health = {"status": "unknown", "error": str(e)}

        return {
            "success": True,
            "qdrant": {
                "health": qdrant_health,
                "stats": qdrant_stats
            },
            "meilisearch": {
                "health": meilisearch_health,
                "stats": meilisearch_stats
            },
            "system_settings": {
                "hash_duplicate_check_enabled": settings.enable_hash_duplicate_check,
                "max_file_size_mb": settings.max_file_size_mb,
                "storage_base_path": settings.storage_base_path
            }
        }

    except Exception as e:
        logger.error(f"Error getting collections status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get collections status: {str(e)}"
        )


@router.post("/admin/collections/qdrant/reset")
async def reset_qdrant_collection(authorization: str = Depends(verify_api_key)):
    """Reset Qdrant collection (delete and recreate)."""
    try:
        # Get current stats before reset
        old_stats = qdrant_service.get_collection_stats()
        old_points = old_stats.get('points_count', 0)

        # Check if client is available
        if not qdrant_service.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Qdrant client not available"
            )

        from qdrant_client.models import VectorParams, Distance

        # Delete existing collection if it exists
        try:
            collections = qdrant_service.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if qdrant_service.collection_name in collection_names:
                logger.info(f"Deleting existing collection: {qdrant_service.collection_name}")
                qdrant_service.client.delete_collection(qdrant_service.collection_name)
                logger.info(f"Collection '{qdrant_service.collection_name}' deleted successfully")
        except Exception as e:
            logger.warning(f"Error deleting collection: {e}")

        # Recreate collection
        logger.info(f"Creating new collection: {qdrant_service.collection_name}")
        qdrant_service.client.create_collection(
            collection_name=qdrant_service.collection_name,
            vectors_config=VectorParams(
                size=settings.vector_dimension,  # 환경변수에서 설정된 벡터 차원
                distance=Distance.COSINE
            )
        )

        logger.info(f"Collection '{qdrant_service.collection_name}' reset successfully")

        return {
            "success": True,
            "message": f"Qdrant collection '{qdrant_service.collection_name}' reset successfully",
            "collection_name": qdrant_service.collection_name,
            "points_deleted": old_points
        }

    except Exception as e:
        logger.error(f"Error resetting Qdrant collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset Qdrant collection: {str(e)}"
        )


@router.post("/admin/collections/meilisearch/reset")
async def reset_meilisearch_index(authorization: str = Depends(verify_api_key)):
    """Reset MeiliSearch index (delete and recreate)."""
    try:
        # Get unified search service
        text_backend = unified_search_service.text_backend

        if not text_backend:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MeiliSearch backend not available"
            )

        # Get current stats
        old_stats = text_backend.get_stats()
        old_docs = old_stats.get('documents_count', 0)

        # Get index name safely
        index_name = getattr(text_backend, 'index_name', 'ragnaforge_documents')

        # Delete existing index
        try:
            await text_backend.delete_index(index_name)
            logger.info(f"Deleted MeiliSearch index: {index_name}")
        except Exception as e:
            logger.warning(f"Error deleting index: {e}")

        # Recreate index
        await text_backend.create_index(index_name)

        # Configure Korean settings if method exists
        if hasattr(text_backend, '_configure_korean_settings'):
            await text_backend._configure_korean_settings()

        logger.info(f"MeiliSearch index '{index_name}' reset successfully")

        return {
            "success": True,
            "message": f"MeiliSearch index '{index_name}' reset successfully",
            "index_name": index_name,
            "documents_deleted": old_docs
        }

    except Exception as e:
        logger.error(f"Error resetting MeiliSearch index: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset MeiliSearch index: {str(e)}"
        )
