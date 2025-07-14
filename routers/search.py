"""Search API routes for vector, text, and hybrid search."""

import logging
from fastapi import APIRouter, HTTPException, Depends, status

from models import (
    VectorSearchRequest, VectorSearchResponse,
    SearchRequest, SearchResponse, SearchResult,
    HybridSearchRequest, HybridSearchResponse,
    SearchStatsResponse
)
from services.search_service import search_service
from services.unified_search_service import unified_search_service
from routers.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")


@router.post("/search", response_model=VectorSearchResponse)
async def vector_search(
    request: VectorSearchRequest,
    authorization: str = Depends(verify_api_key)
):
    """Perform vector similarity search across document chunks."""
    try:
        result = await search_service.vector_search(
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold,
            document_filter=request.document_filter,
            embedding_model=request.embedding_model
        )
        return VectorSearchResponse(**result)
    except Exception as e:
        logger.error(f"Error in vector search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {str(e)}"
        )


@router.post("/search/vector", response_model=SearchResponse)
async def unified_vector_search(
    request: SearchRequest,
    authorization: str = Depends(verify_api_key)
):
    """Perform vector similarity search using the unified search service."""
    try:
        if not unified_search_service.is_initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unified search service not initialized"
            )

        result = await unified_search_service.vector_search(
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold,
            filters=request.filters,
            embedding_model=request.embedding_model,
            rerank=request.rerank,
            rerank_top_k=request.rerank_top_k
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Vector search failed")
            )

        # Convert raw results to SearchResult format
        search_results = []
        for item in result.get("results", []):
            metadata = item.get("metadata", {})
            # Extract content from metadata.text (Qdrant stores text content here)
            content = metadata.get("text", "")

            search_result = SearchResult(
                id=str(item.get("id", "")),
                score=item.get("score", 0.0),
                metadata=metadata,
                content=content,
                highlights=item.get("highlights"),
                search_source="vector"
            )
            search_results.append(search_result)

        return SearchResponse(
            success=result.get("success", True),
            results=search_results,
            total_results=result.get("total_results", len(search_results)),
            search_type=result.get("search_type", "vector"),
            query=result.get("query", request.query),
            search_time=result.get("search_time", 0.0),
            backend=result.get("backend", ""),
            error=result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified vector search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {str(e)}"
        )


@router.post("/search/text", response_model=SearchResponse)
async def unified_text_search(
    request: SearchRequest,
    authorization: str = Depends(verify_api_key)
):
    """Perform text search using the unified search service."""
    try:
        if not unified_search_service.is_initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unified search service not initialized"
            )

        result = await unified_search_service.text_search(
            query=request.query,
            limit=request.limit,
            filters=request.filters,
            highlight=request.highlight
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Text search failed")
            )

        return SearchResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified text search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text search failed: {str(e)}"
        )


@router.post("/search/hybrid", response_model=HybridSearchResponse)
async def unified_hybrid_search(
    request: HybridSearchRequest,
    authorization: str = Depends(verify_api_key)
):
    """Perform hybrid search combining vector and text search."""
    try:
        if not unified_search_service.is_initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unified search service not initialized"
            )

        result = await unified_search_service.hybrid_search(
            query=request.query,
            limit=request.limit,
            vector_weight=request.vector_weight,
            text_weight=request.text_weight,
            score_threshold=request.score_threshold,
            filters=request.filters,
            embedding_model=request.embedding_model,
            highlight=request.highlight,
            rerank=request.rerank,
            rerank_top_k=request.rerank_top_k
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Hybrid search failed")
            )

        # Convert raw results to SearchResult format
        search_results = []
        for item in result.get("results", []):
            metadata = item.get("metadata", {})

            # Extract content properly based on search source
            # Vector search results: content is in metadata.text (from Qdrant payload)
            # Text search results: content is in item.content (from MeiliSearch)
            # Hybrid search: could be either, so check both
            content = ""
            if "content" in item and item["content"]:
                # Text search result or already processed content
                content = item["content"]
            elif "text" in metadata and metadata["text"]:
                # Vector search result from Qdrant payload
                content = metadata["text"]
            elif "content" in metadata and metadata["content"]:
                # Alternative content location
                content = metadata["content"]
            else:
                # Fallback to empty content
                content = ""

            search_result = SearchResult(
                id=str(item.get("id", "")),
                score=item.get("hybrid_score", item.get("score", 0.0)),
                metadata=metadata,
                content=content,
                highlights=item.get("highlights"),
                search_source=item.get("search_source", "hybrid")
            )
            search_results.append(search_result)

        return HybridSearchResponse(
            success=result.get("success", True),
            results=search_results,
            total_results=result.get("total_results", len(search_results)),
            search_type=result.get("search_type", "hybrid"),
            query=result.get("query", request.query),
            search_time=result.get("search_time", 0.0),
            backend=result.get("backend"),
            error=result.get("error"),
            vector_results_count=result.get("vector_results_count", 0),
            text_results_count=result.get("text_results_count", 0),
            weights=result.get("weights", {}),
            backends=result.get("backends", {})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified hybrid search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid search failed: {str(e)}"
        )


@router.get("/search/stats")
async def get_search_stats(authorization: str = Depends(verify_api_key)):
    """Get comprehensive search service statistics."""
    try:
        stats = search_service.get_search_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting search stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get search stats: {str(e)}"
        )
