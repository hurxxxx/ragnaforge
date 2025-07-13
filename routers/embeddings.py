"""Embedding and similarity API routes."""

import logging
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List

from models import (
    EmbeddingRequest, EmbeddingResponse, EmbeddingData,
    SimilarityRequest, SimilarityResponse,
    ModelsResponse, ModelInfo,
    HealthResponse
)
from services import embedding_service
from config import settings
from routers.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        is_model_loaded=embedding_service.is_model_loaded(),
        version=settings.app_version
    )


@router.get("/memory")
async def memory_info():
    """Get memory usage information."""
    return embedding_service.get_memory_info()


@router.post("/memory/cleanup")
async def cleanup_memory():
    """Clean up GPU memory."""
    embedding_service.cleanup_memory()
    return {"status": "memory cleaned", "info": embedding_service.get_memory_info()}


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    """List available models."""
    models = embedding_service.get_available_models()
    return ModelsResponse(
        object="list",
        data=[ModelInfo(**model) for model in models]
    )


@router.post("/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(
    request: EmbeddingRequest,
    authorization: str = Depends(verify_api_key)
):
    """Generate embeddings for input texts."""
    try:
        # Get model name
        model_name = request.model or settings.default_model

        # Generate embeddings
        embeddings = embedding_service.encode_texts(request.input, model_name)

        # Format response
        embedding_data = [
            EmbeddingData(
                embedding=embedding.tolist(),
                index=i
            )
            for i, embedding in enumerate(embeddings)
        ]

        return EmbeddingResponse(
            object="list",
            data=embedding_data,
            model=model_name,
            usage={
                "prompt_tokens": sum(len(text.split()) for text in request.input),
                "total_tokens": sum(len(text.split()) for text in request.input)
            }
        )

    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embeddings: {str(e)}"
        )


@router.post("/similarity", response_model=SimilarityResponse)
async def calculate_similarity(
    request: SimilarityRequest,
    authorization: str = Depends(verify_api_key)
):
    """Calculate similarity matrix between texts."""
    try:
        # Get model name
        model_name = request.model or settings.default_model

        # Calculate similarity
        similarity_matrix = embedding_service.calculate_similarity(request.texts, model_name)

        return SimilarityResponse(
            similarities=similarity_matrix.tolist(),
            model=model_name
        )

    except Exception as e:
        logger.error(f"Error calculating similarity: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate similarity: {str(e)}"
        )
