"""Pydantic models for API request/response validation."""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator


class EmbeddingRequest(BaseModel):
    """Request model for embedding generation."""

    input: Union[str, List[str]] = Field(
        ...,
        description="Text or list of texts to embed",
        example=["안녕하세요", "한국어 임베딩 모델입니다"]
    )
    model: Optional[str] = Field(
        None,
        description="Model to use for embedding",
        example="nlpai-lab/KURE-v1"
    )
    encoding_format: Optional[str] = Field(
        "float",
        description="Encoding format for embeddings",
        example="float"
    )
    dimensions: Optional[int] = Field(
        None,
        description="Number of dimensions for the embedding",
        example=768
    )
    user: Optional[str] = Field(
        None,
        description="A unique identifier representing your end-user",
        example="user-123"
    )

    @validator('input')
    def validate_input(cls, v):
        if isinstance(v, str):
            if len(v) > 8192:
                raise ValueError("Text length exceeds maximum limit of 8192 characters")
            return [v]
        elif isinstance(v, list):
            if len(v) > 32:
                raise ValueError("Batch size exceeds maximum limit of 32")
            for text in v:
                if not isinstance(text, str):
                    raise ValueError("All inputs must be strings")
                if len(text) > 8192:
                    raise ValueError("Text length exceeds maximum limit of 8192 characters")
            return v
        else:
            raise ValueError("Input must be a string or list of strings")


class EmbeddingData(BaseModel):
    """Individual embedding data."""

    object: str = "embedding"
    embedding: List[float] = Field(..., description="The embedding vector")
    index: int = Field(..., description="Index of the input text")


class EmbeddingResponse(BaseModel):
    """Response model for embedding generation."""

    object: str = "list"
    data: List[EmbeddingData] = Field(..., description="List of embeddings")
    model: str = Field(..., description="Model used for embedding")
    usage: dict = Field(..., description="Usage statistics")


class SimilarityRequest(BaseModel):
    """Request model for similarity calculation."""

    texts: List[str] = Field(
        ...,
        min_items=2,
        max_items=32,
        description="List of texts to compare",
        example=["첫 번째 텍스트", "두 번째 텍스트"]
    )
    model: Optional[str] = Field(
        None,
        description="Model to use for similarity calculation",
        example="nlpai-lab/KURE-v1"
    )

    @validator('texts')
    def validate_texts(cls, v):
        for text in v:
            if len(text) > 8192:
                raise ValueError("Text length exceeds maximum limit of 8192 characters")
        return v


class SimilarityResponse(BaseModel):
    """Response model for similarity calculation."""

    similarities: List[List[float]] = Field(
        ...,
        description="Similarity matrix between texts"
    )
    model: str = Field(..., description="Model used for similarity calculation")


class ModelInfo(BaseModel):
    """Model information."""

    id: str = Field(..., description="Model identifier")
    object: str = "model"
    created: int = Field(..., description="Creation timestamp")
    owned_by: str = Field(..., description="Model owner")


class ModelsResponse(BaseModel):
    """Response model for available models."""

    object: str = "list"
    data: List[ModelInfo] = Field(..., description="List of available models")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    is_model_loaded: bool = Field(..., description="Whether model is loaded")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: dict = Field(..., description="Error details")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": {
                    "message": "Invalid input",
                    "type": "invalid_request_error",
                    "code": "invalid_input"
                }
            }
        }
    }
