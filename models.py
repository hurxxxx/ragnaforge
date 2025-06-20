"""Pydantic models for API request/response validation."""

from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, validator
from config import settings


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
            if len(v) > settings.max_batch_size:
                raise ValueError(f"Batch size exceeds maximum limit of {settings.max_batch_size}")
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


class ChunkRequest(BaseModel):
    """Request model for text chunking."""

    text: str = Field(
        ...,
        description="Text to be chunked",
        example="이것은 긴 텍스트입니다. 여러 문장으로 구성되어 있습니다. 청킹 기능을 테스트하기 위한 예제입니다."
    )
    strategy: Optional[str] = Field(
        None,
        description="Chunking strategy (sentence, recursive, token). Uses default from settings if not provided.",
        example="recursive"
    )
    chunk_size: Optional[int] = Field(
        None,
        ge=50,
        le=8192,
        description="Maximum chunk size in tokens. Uses default from settings if not provided.",
        example=380
    )
    overlap: Optional[int] = Field(
        None,
        ge=0,
        le=500,
        description="Overlap between chunks in tokens. Uses default from settings if not provided.",
        example=70
    )
    language: Optional[str] = Field(
        None,
        description="Language for chunking (auto, ko, en). Uses default from settings if not provided.",
        example="auto"
    )

    @validator('strategy')
    def validate_strategy(cls, v):
        if v is not None:
            allowed_strategies = ["sentence", "recursive", "token"]
            if v not in allowed_strategies:
                raise ValueError(f"Strategy must be one of {allowed_strategies}")
        return v

    @validator('language')
    def validate_language(cls, v):
        if v is not None:
            allowed_languages = ["auto", "ko", "en"]
            if v not in allowed_languages:
                raise ValueError(f"Language must be one of {allowed_languages}")
        return v

    @validator('overlap')
    def validate_overlap(cls, v, values):
        if v is not None and 'chunk_size' in values and values['chunk_size'] is not None:
            if v >= values['chunk_size']:
                raise ValueError("Overlap must be less than chunk_size")
        return v


class ChunkData(BaseModel):
    """Individual chunk data."""

    text: str = Field(..., description="Chunk text content")
    index: int = Field(..., description="Chunk index")
    start_char: int = Field(..., description="Start character position in original text")
    end_char: int = Field(..., description="End character position in original text")
    token_count: int = Field(..., description="Estimated token count")


class ChunkResponse(BaseModel):
    """Response model for text chunking."""

    object: str = "list"
    data: List[ChunkData] = Field(..., description="List of text chunks")
    total_chunks: int = Field(..., description="Total number of chunks")
    strategy: str = Field(..., description="Chunking strategy used")
    original_length: int = Field(..., description="Original text length in characters")
    total_tokens: int = Field(..., description="Total estimated tokens across all chunks")


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


# Document conversion models
class DocumentConversionRequest(BaseModel):
    """Request for document conversion."""

    file_path: str = Field(..., description="Path to the PDF file to convert")
    output_dir: Optional[str] = Field(None, description="Directory to save output files")
    extract_images: bool = Field(True, description="Whether to extract images")


class DocumentConversionResponse(BaseModel):
    """Response for document conversion."""

    success: bool = Field(..., description="Whether conversion was successful")
    library: str = Field(..., description="Library used for conversion")
    conversion_time: float = Field(..., description="Time taken for conversion in seconds")
    file_size_mb: float = Field(..., description="Size of input file in MB")
    markdown: Optional[str] = Field(None, description="Generated markdown content")
    markdown_length: Optional[int] = Field(None, description="Length of generated markdown")
    images_count: Optional[int] = Field(None, description="Number of images found")
    gpu_memory_used_gb: Optional[float] = Field(None, description="GPU memory used in GB")
    saved_files: Optional[List[str]] = Field(None, description="List of saved output files")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")
    error: Optional[str] = Field(None, description="Error message if conversion failed")


class ConversionComparisonResponse(BaseModel):
    """Response for conversion comparison."""

    marker_result: DocumentConversionResponse = Field(..., description="Marker conversion result")
    docling_result: DocumentConversionResponse = Field(..., description="Docling conversion result")
    comparison: Dict[str, Any] = Field(..., description="Performance comparison metrics")
