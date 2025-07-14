"""Reranking API routes."""

import logging
from fastapi import APIRouter, HTTPException, Depends, status

from models import RerankRequest, RerankResponse, RerankResult
from services.rerank_service import rerank_service
from routers.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")


@router.post("/rerank", response_model=RerankResponse)
async def rerank_documents(
    request: RerankRequest,
    authorization: str = Depends(verify_api_key)
):
    """Re-rank documents based on query relevance using cross-encoder models."""
    try:
        # Convert RerankDocument to dict format expected by service
        documents = []
        for doc in request.documents:
            doc_dict = {
                "id": doc.id,
                "text": doc.text,
                "score": doc.score,
                "metadata": doc.metadata or {}
            }
            documents.append(doc_dict)

        # Perform reranking
        result = await rerank_service.rerank_documents(
            query=request.query,
            documents=documents,
            top_k=request.top_k,
            use_cache=True
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Reranking failed")
            )

        # Convert back to RerankResult format
        reranked_results = []
        for i, doc in enumerate(result.get("documents", []), 1):
            rerank_result = RerankResult(
                id=doc.get("id"),
                text=doc.get("text"),
                score=doc.get("score", doc.get("rerank_score", 0.0)),
                rerank_score=doc.get("rerank_score", doc.get("score", 0.0)),
                original_score=doc.get("original_score"),
                rank_position=i,
                metadata=doc.get("metadata", {})
            )
            reranked_results.append(rerank_result)

        return RerankResponse(
            success=True,
            results=reranked_results,
            query=request.query,
            total_count=len(documents),
            reranked_count=len(reranked_results),
            processing_time=result.get("processing_time", 0.0),
            model_info=result.get("model_info", {}),
            rerank_applied=result.get("rerank_applied", True),
            from_cache=result.get("from_cache", False)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reranking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reranking failed: {str(e)}"
        )


@router.get("/rerank/models")
async def get_rerank_models(authorization: str = Depends(verify_api_key)):
    """Get information about available rerank models."""
    try:
        from services.rerank.rerank_factory import RerankFactory

        available_models = RerankFactory.get_available_models()
        current_model = rerank_service.get_model_info()

        return {
            "success": True,
            "available_models": available_models,
            "current_model": current_model,
            "rerank_enabled": rerank_service.is_enabled()
        }

    except Exception as e:
        logger.error(f"Error getting rerank models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rerank models: {str(e)}"
        )


@router.get("/rerank/health")
async def get_rerank_health(authorization: str = Depends(verify_api_key)):
    """Check rerank service health."""
    try:
        health_info = {
            "enabled": rerank_service.is_enabled(),
            "model_loaded": rerank_service.is_model_loaded() if rerank_service.is_enabled() else False,
            "model_info": rerank_service.get_model_info() if rerank_service.is_enabled() else None
        }
        
        return {
            "success": True,
            "status": "healthy" if health_info["enabled"] else "disabled",
            **health_info
        }

    except Exception as e:
        logger.error(f"Error checking rerank health: {str(e)}")
        return {
            "success": False,
            "status": "error",
            "error": str(e)
        }
