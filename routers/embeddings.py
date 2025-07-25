"""Embedding and similarity API routes."""

import logging
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
from pydantic import ValidationError

from models import (
    EmbeddingRequest, EmbeddingResponse, EmbeddingData,
    SimilarityRequest, SimilarityResponse,
    ModelsResponse, ModelInfo,
    HealthResponse
)
from services import embedding_service
from config import settings
from routers.auth import verify_api_key
from utils.openai_errors import (
    model_not_found_error,
    invalid_input_error,
    internal_server_error,
    handle_validation_error,
    handle_generic_error
)

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
    """Generate embeddings for input texts - OpenAI API compatible."""
    try:
        # Get model name
        model_name = request.model or settings.default_model

        # Validate model exists
        if model_name not in settings.available_models:
            raise model_not_found_error(model_name)

        # Convert input to list if string
        input_texts = request.input if isinstance(request.input, list) else [request.input]

        # Enhanced input validation
        if not input_texts:
            raise invalid_input_error("Input cannot be empty")

        # Validate each text input
        for i, text in enumerate(input_texts):
            if not isinstance(text, str):
                raise invalid_input_error(f"Input at index {i} must be a string, got {type(text).__name__}")
            if not text.strip():
                raise invalid_input_error(f"Input at index {i} cannot be empty or whitespace only")
            if len(text) > 32000:  # Conservative character limit
                raise invalid_input_error(f"Input at index {i} is too long ({len(text)} characters). Maximum is 32000 characters.")

        # Validate batch size
        if len(input_texts) > 2048:
            raise invalid_input_error(f"Batch size too large ({len(input_texts)}). Maximum is 2048 inputs.")

        # Ensure model is loaded
        if not embedding_service.is_model_loaded(model_name):
            logger.info(f"Loading model {model_name} for embedding request")
            try:
                embedding_service.load_model(model_name)
            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                raise internal_server_error(f"Failed to load model {model_name}")

        # Count tokens using the model's tokenizer
        try:
            token_counts = embedding_service.count_tokens_batch(input_texts, model_name)
            total_tokens = sum(token_counts)

            # Validate token limits
            max_tokens_per_input = 8192
            for i, token_count in enumerate(token_counts):
                if token_count > max_tokens_per_input:
                    raise invalid_input_error(f"Input at index {i} exceeds token limit ({token_count} > {max_tokens_per_input})")

            # Check total token limit
            if total_tokens > 1000000:
                raise invalid_input_error(f"Total tokens exceed limit ({total_tokens} > 1000000)")

        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Token counting failed: {e}")
            raise internal_server_error("Failed to count tokens")

        # Generate embeddings with safety checks
        try:
            embeddings = embedding_service.encode_texts(input_texts, model_name)

            # Validate embedding output
            if embeddings is None:
                raise internal_server_error("Embedding generation returned None")
            if len(embeddings) != len(input_texts):
                raise internal_server_error(f"Embedding count mismatch: expected {len(input_texts)}, got {len(embeddings)}")

        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Embedding generation failed: {e}")
            raise internal_server_error("Failed to generate embeddings")

        # Format response with validation
        try:
            embedding_data = []
            for i, embedding in enumerate(embeddings):
                if embedding is None:
                    raise internal_server_error(f"Embedding at index {i} is None")

                # Convert to list with error handling
                try:
                    embedding_list = embedding.tolist()
                except Exception as e:
                    logger.error(f"Failed to convert embedding {i} to list: {e}")
                    raise internal_server_error(f"Failed to format embedding at index {i}")

                embedding_data.append(EmbeddingData(
                    embedding=embedding_list,
                    index=i
                ))

            return EmbeddingResponse(
                object="list",
                data=embedding_data,
                model=model_name,
                usage={
                    "prompt_tokens": total_tokens,
                    "total_tokens": total_tokens
                }
            )

        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            logger.error(f"Response formatting failed: {e}")
            raise internal_server_error("Failed to format response")

    except HTTPException:
        # Re-raise HTTP exceptions (already in OpenAI format)
        raise
    except ValidationError as e:
        # Handle Pydantic validation errors
        logger.error(f"Validation error in embeddings: {str(e)}")
        raise handle_validation_error(e)
    except ValueError as e:
        # Handle value errors (e.g., from token validation)
        logger.error(f"Value error in embeddings: {str(e)}")
        raise invalid_input_error(str(e))
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error generating embeddings: {str(e)}")
        raise handle_generic_error(e, "generating embeddings")


@router.post("/similarity", response_model=SimilarityResponse)
async def calculate_similarity(
    request: SimilarityRequest,
    authorization: str = Depends(verify_api_key)
):
    """Calculate similarity matrix between texts."""
    try:
        # Get model name
        model_name = request.model or settings.default_model

        # Validate model exists
        if model_name not in settings.available_models:
            raise model_not_found_error(model_name)

        # Calculate similarity
        similarity_matrix = embedding_service.calculate_similarity(request.texts, model_name)

        return SimilarityResponse(
            similarities=similarity_matrix.tolist(),
            model=model_name
        )

    except HTTPException:
        # Re-raise HTTP exceptions (already in OpenAI format)
        raise
    except ValidationError as e:
        # Handle Pydantic validation errors
        logger.error(f"Validation error in similarity: {str(e)}")
        raise handle_validation_error(e)
    except ValueError as e:
        # Handle value errors
        logger.error(f"Value error in similarity: {str(e)}")
        raise invalid_input_error(str(e))
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error calculating similarity: {str(e)}")
        raise handle_generic_error(e, "calculating similarity")
