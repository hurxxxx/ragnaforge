"""Pydantic models for API request/response validation."""

from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
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
        example="dragonkue/snowflake-arctic-embed-l-v2.0-ko"
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


# File Upload Models
class SupportedFileType(str, Enum):
    """Supported file types for upload."""
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    TXT = "txt"
    MD = "md"


class FileUploadResponse(BaseModel):
    """Response for file upload."""

    success: bool = Field(..., description="Whether the upload was successful")
    file_id: str = Field(..., description="Unique identifier for the uploaded file")
    filename: str = Field(..., description="Original filename")
    file_type: SupportedFileType = Field(..., description="Detected file type")
    file_size: int = Field(..., description="File size in bytes")
    upload_time: float = Field(..., description="Time taken to upload and process")
    temp_path: str = Field(..., description="File storage path")
    storage_path: Optional[str] = Field(None, description="Organized storage path")
    relative_path: Optional[str] = Field(None, description="Relative path from storage base")
    error: Optional[str] = Field(None, description="Error message if upload failed")


class DocumentProcessRequest(BaseModel):
    """Request for processing uploaded document."""

    file_id: str = Field(..., description="File ID from upload response")
    conversion_method: Optional[str] = Field(
        "auto",
        description="Conversion method: 'marker', 'docling', or 'auto'",
        example="auto"
    )
    extract_images: bool = Field(False, description="Whether to extract images")
    chunk_strategy: Optional[str] = Field(
        None,
        description="Text chunking strategy",
        example="recursive"
    )
    chunk_size: Optional[int] = Field(
        None,
        description="Chunk size for text splitting",
        example=380
    )
    overlap: Optional[int] = Field(
        None,
        description="Overlap size between chunks",
        example=70
    )
    generate_embeddings: bool = Field(
        True,
        description="Whether to generate embeddings for chunks"
    )
    embedding_model: Optional[str] = Field(
        None,
        description="Model to use for embeddings",
        example="dragonkue/snowflake-arctic-embed-l-v2.0-ko"
    )


class DocumentProcessResponse(BaseModel):
    """Response for document processing."""

    success: bool = Field(..., description="Whether processing was successful")
    file_id: str = Field(..., description="File ID")
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    conversion_method: str = Field(..., description="Conversion method used")
    conversion_time: float = Field(..., description="Time taken for conversion")
    markdown_content: str = Field(..., description="Converted markdown content")
    markdown_length: int = Field(..., description="Length of markdown content")
    total_chunks: int = Field(..., description="Number of text chunks created")
    chunks: List[Dict[str, Any]] = Field(..., description="Text chunks with metadata")
    embeddings_generated: bool = Field(..., description="Whether embeddings were generated")
    processing_time: float = Field(..., description="Total processing time")
    error: Optional[str] = Field(None, description="Error message if processing failed")


# Vector Search Models
class VectorSearchRequest(BaseModel):
    """Request for vector similarity search."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)
    score_threshold: float = Field(0.0, description="Minimum similarity score", ge=0.0, le=1.0)
    document_filter: Optional[Dict[str, Any]] = Field(
        None,
        description="Filter by document properties",
        example={"file_types": ["pdf"], "document_ids": ["doc1", "doc2"]}
    )
    embedding_model: Optional[str] = Field(
        None,
        description="Model to use for query embedding",
        example="nlpai-lab/KURE-v1"
    )


class SearchResult(BaseModel):
    """Individual search result."""

    id: str = Field(..., description="Chunk ID")
    score: float = Field(..., description="Similarity score")
    document_id: str = Field(..., description="Source document ID")
    chunk_index: int = Field(..., description="Chunk index in document")
    text: str = Field(..., description="Chunk text content")
    filename: str = Field(..., description="Source filename")
    file_type: str = Field(..., description="Source file type")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")


class VectorSearchResponse(BaseModel):
    """Response for vector similarity search."""

    success: bool = Field(..., description="Whether search was successful")
    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Number of results found")
    search_time: float = Field(..., description="Time taken for search")
    results: List[SearchResult] = Field(..., description="Search results")
    error: Optional[str] = Field(None, description="Error message if search failed")


class QdrantStatsResponse(BaseModel):
    """Response for Qdrant statistics."""

    collection_name: str = Field(..., description="Collection name")
    points_count: int = Field(..., description="Total number of points")
    vectors_count: int = Field(..., description="Total number of vectors")
    indexed_vectors_count: int = Field(..., description="Number of indexed vectors")
    status: str = Field(..., description="Collection status")
    disk_data_size: int = Field(..., description="Disk data size in bytes")
    ram_data_size: int = Field(..., description="RAM data size in bytes")


# Storage Management Models
class StorageStatsResponse(BaseModel):
    """Response for storage statistics."""

    success: bool = Field(..., description="Whether the request was successful")
    stats: Dict[str, Any] = Field(..., description="Storage statistics")


class StorageFileInfo(BaseModel):
    """Information about a stored file."""

    name: str = Field(..., description="File name")
    path: str = Field(..., description="File path")
    size: int = Field(..., description="File size in bytes")
    created: str = Field(..., description="Creation timestamp")
    modified: str = Field(..., description="Modification timestamp")
    is_file: bool = Field(..., description="Whether it's a file")
    is_dir: bool = Field(..., description="Whether it's a directory")
    relative_path: Optional[str] = Field(None, description="Relative path from storage base")


class StorageFilesResponse(BaseModel):
    """Response for listing storage files."""

    success: bool = Field(..., description="Whether the request was successful")
    directory_type: str = Field(..., description="Directory type")
    file_type: Optional[str] = Field(None, description="File type filter")
    files: List[StorageFileInfo] = Field(..., description="List of files")
    count: int = Field(..., description="Number of files")


class StorageCleanupResponse(BaseModel):
    """Response for storage cleanup."""

    success: bool = Field(..., description="Whether the cleanup was successful")
    deleted_count: int = Field(..., description="Number of files deleted")
    max_age_hours: int = Field(..., description="Maximum age in hours for cleanup")


class FileInfoResponse(BaseModel):
    """Response for file information."""

    success: bool = Field(..., description="Whether the request was successful")
    file_info: Dict[str, Any] = Field(..., description="File information")
