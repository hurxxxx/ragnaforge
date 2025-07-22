"""Pydantic models for API request/response validation."""

from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from config import settings


class EmbeddingRequest(BaseModel):
    """Request model for embedding generation."""

    input: Union[str, List[str]] = Field(
        ...,
        description="Text or list of texts to embed",
        examples=[["안녕하세요", "한국어 임베딩 모델입니다"]]
    )
    model: Optional[str] = Field(
        None,
        description="Model to use for embedding",
        examples=["dragonkue/snowflake-arctic-embed-l-v2.0-ko"]
    )
    encoding_format: Optional[str] = Field(
        "float",
        description="Encoding format for embeddings",
        examples=["float"]
    )
    dimensions: Optional[int] = Field(
        None,
        description="Number of dimensions for the embedding",
        examples=[768]
    )
    user: Optional[str] = Field(
        None,
        description="A unique identifier representing your end-user",
        examples=["user-123"]
    )

    @field_validator('input')
    @classmethod
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
        min_length=2,
        max_length=32,
        description="List of texts to compare",
        examples=[["첫 번째 텍스트", "두 번째 텍스트"]]
    )
    model: Optional[str] = Field(
        None,
        description="Model to use for similarity calculation",
        examples=["nlpai-lab/KURE-v1"]
    )

    @field_validator('texts')
    @classmethod
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
        examples=["이것은 긴 텍스트입니다. 여러 문장으로 구성되어 있습니다. 청킹 기능을 테스트하기 위한 예제입니다."]
    )
    strategy: Optional[str] = Field(
        None,
        description="Chunking strategy (sentence, recursive, token). Uses default from settings if not provided.",
        examples=["recursive"]
    )
    chunk_size: Optional[int] = Field(
        None,
        ge=50,
        le=8192,
        description="Maximum chunk size in tokens. Uses default from settings if not provided.",
        examples=[380]
    )
    overlap: Optional[int] = Field(
        None,
        ge=0,
        le=500,
        description="Overlap between chunks in tokens. Uses default from settings if not provided.",
        examples=[70]
    )
    language: Optional[str] = Field(
        None,
        description="Language for chunking (auto, ko, en). Uses default from settings if not provided.",
        examples=["auto"]
    )

    @field_validator('strategy')
    @classmethod
    def validate_strategy(cls, v):
        if v is not None:
            allowed_strategies = ["token", "sentence", "recursive", "semantic"]
            if v not in allowed_strategies:
                raise ValueError(f"Strategy must be one of {allowed_strategies}")
        return v

    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        if v is not None:
            allowed_languages = ["auto", "ko", "en"]
            if v not in allowed_languages:
                raise ValueError(f"Language must be one of {allowed_languages}")
        return v

    @field_validator('overlap')
    @classmethod
    def validate_overlap(cls, v, info):
        if v is not None and info.data.get('chunk_size') is not None:
            if v >= info.data['chunk_size']:
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

    # Duplicate detection fields
    duplicate_detected: Optional[bool] = Field(False, description="Whether a duplicate file was detected")
    existing_file: Optional[dict] = Field(None, description="Information about existing duplicate file")
    file_hash: Optional[str] = Field(None, description="SHA-256 hash of the file")
    upload_count: Optional[int] = Field(1, description="Number of times this file has been uploaded")
    message: Optional[str] = Field(None, description="Additional message about the upload")


class DocumentProcessRequest(BaseModel):
    """Request for processing uploaded document."""

    file_id: str = Field(..., description="File ID from upload response")
    conversion_method: Optional[str] = Field(
        "auto",
        description="Conversion method: 'marker', 'docling', or 'auto'",
        examples=["auto"]
    )
    extract_images: bool = Field(False, description="Whether to extract images")
    chunk_strategy: Optional[str] = Field(
        None,
        description="Text chunking strategy",
        examples=["recursive"]
    )
    chunk_size: Optional[int] = Field(
        None,
        description="Chunk size for text splitting",
        examples=[380]
    )
    overlap: Optional[int] = Field(
        None,
        description="Overlap size between chunks",
        examples=[70]
    )
    generate_embeddings: bool = Field(
        True,
        description="Whether to generate embeddings for chunks"
    )
    embedding_model: Optional[str] = Field(
        None,
        description="Model to use for embeddings",
        examples=["dragonkue/snowflake-arctic-embed-l-v2.0-ko"]
    )
    enable_hash_check: Optional[bool] = Field(
        None,
        description="Whether to enable hash-based duplicate detection for this request. If None, uses system default setting."
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

    # Duplicate detection fields
    duplicate_detected: Optional[bool] = Field(False, description="Whether a duplicate document was detected")
    existing_document: Optional[bool] = Field(False, description="Whether this document was already processed")
    original_filename: Optional[str] = Field(None, description="Original filename of the existing document")
    original_processing_time: Optional[float] = Field(None, description="Processing time of the original document")
    original_created_at: Optional[float] = Field(None, description="Creation time of the original document")
    message: Optional[str] = Field(None, description="Additional message about duplicate detection")


# Vector Search Models
class VectorSearchRequest(BaseModel):
    """Request for vector similarity search."""

    query: str = Field(..., description="Search query text", min_length=1)
    limit: int = Field(default_factory=lambda: settings.default_search_limit, description="Maximum number of results", ge=1, le=1000)
    score_threshold: float = Field(default_factory=lambda: settings.default_score_threshold, description="Minimum similarity score", ge=0.0, le=1.0)
    document_filter: Optional[Dict[str, Any]] = Field(
        None,
        description="Filter by document properties",
        examples=[{"file_types": ["pdf"], "document_ids": ["doc1", "doc2"]}]
    )
    embedding_model: Optional[str] = Field(
        None,
        description="Model to use for query embedding",
        examples=["nlpai-lab/KURE-v1"]
    )


class VectorSearchResult(BaseModel):
    """Individual vector search result."""

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
    results: List[VectorSearchResult] = Field(..., description="Search results")
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


class FileInfo(BaseModel):
    """File information with duplicate detection data."""

    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type")
    file_size: int = Field(..., description="File size in bytes")
    upload_time: float = Field(..., description="Upload timestamp")
    created_at: float = Field(..., description="Creation timestamp")

    # Duplicate detection fields
    file_hash: Optional[str] = Field(None, description="SHA-256 hash of the file")
    upload_count: int = Field(1, description="Number of times this file has been uploaded")
    is_duplicate: bool = Field(False, description="Whether this file is a duplicate")

    # Processing status
    is_processed: bool = Field(False, description="Whether this file has been processed")
    document_id: Optional[str] = Field(None, description="Associated document ID if processed")


class FileListResponse(BaseModel):
    """Response for file listing."""

    success: bool = Field(..., description="Whether the request was successful")
    files: List[FileInfo] = Field(..., description="List of files")
    total: int = Field(..., description="Total number of files")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of files per page")
    total_pages: int = Field(..., description="Total number of pages")


class DuplicateGroup(BaseModel):
    """Information about a group of duplicate files."""

    file_hash: str = Field(..., description="SHA-256 hash of the duplicate files")
    files: List[FileInfo] = Field(..., description="List of duplicate files")
    total_uploads: int = Field(..., description="Total number of uploads for this content")
    first_uploaded: float = Field(..., description="Timestamp of first upload")
    last_uploaded: float = Field(..., description="Timestamp of last upload")
    is_processed: bool = Field(False, description="Whether any file in this group has been processed")
    document_id: Optional[str] = Field(None, description="Associated document ID if processed")


class DuplicateStatsResponse(BaseModel):
    """Response for duplicate file statistics."""

    success: bool = Field(..., description="Whether the request was successful")
    total_files: int = Field(..., description="Total number of files")
    unique_files: int = Field(..., description="Number of unique files (by hash)")
    duplicate_groups: int = Field(..., description="Number of duplicate groups")
    total_duplicates: int = Field(..., description="Total number of duplicate files")
    storage_saved_bytes: int = Field(..., description="Storage space saved by deduplication")


class DuplicateListResponse(BaseModel):
    """Response for listing duplicate file groups."""

    success: bool = Field(..., description="Whether the request was successful")
    duplicate_groups: List[DuplicateGroup] = Field(..., description="List of duplicate groups")
    total_groups: int = Field(..., description="Total number of duplicate groups")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of groups per page")
    total_pages: int = Field(..., description="Total number of pages")


class DataConsistencyResponse(BaseModel):
    """Response for data consistency check."""

    success: bool = Field(..., description="Whether the check was successful")
    consistent: bool = Field(..., description="Whether data is consistent")
    issues_found: int = Field(..., description="Number of issues found")
    issues: List[Dict[str, Any]] = Field(..., description="List of consistency issues")
    checked_at: float = Field(..., description="Timestamp when check was performed")
    error: Optional[str] = Field(None, description="Error message if check failed")


class DataRepairResponse(BaseModel):
    """Response for data repair operation."""

    success: bool = Field(..., description="Whether the repair was successful")
    dry_run: bool = Field(..., description="Whether this was a dry run")
    repairs_performed: int = Field(..., description="Number of repairs performed")
    repairs: List[Dict[str, Any]] = Field(..., description="List of repairs performed")
    repaired_at: float = Field(..., description="Timestamp when repair was performed")
    error: Optional[str] = Field(None, description="Error message if repair failed")




class DuplicateAnalyticsResponse(BaseModel):
    """Response for duplicate detection analytics."""

    success: bool = Field(..., description="Whether the request was successful")
    period_hours: int = Field(..., description="Analysis period in hours")
    total_duplicates: int = Field(..., description="Total number of duplicates detected")
    unique_files: int = Field(..., description="Number of unique files")
    storage_saved_bytes: int = Field(..., description="Storage space saved in bytes")
    storage_saved_mb: float = Field(..., description="Storage space saved in MB")
    detection_methods: Dict[str, int] = Field(..., description="Distribution of detection methods")
    file_types: Dict[str, int] = Field(..., description="Distribution of file types")
    top_duplicated_files: List[Dict[str, Any]] = Field(..., description="Most duplicated files")
    hourly_distribution: Dict[str, int] = Field(..., description="Hourly distribution of duplicates")


class PerformanceAnalyticsResponse(BaseModel):
    """Response for performance analytics."""

    success: bool = Field(..., description="Whether the request was successful")
    period_hours: int = Field(..., description="Analysis period in hours")
    total_operations: int = Field(..., description="Total number of operations")
    success_rate: float = Field(..., description="Success rate percentage")
    average_duration_ms: float = Field(..., description="Average operation duration in milliseconds")
    operations: Dict[str, Dict[str, float]] = Field(..., description="Per-operation statistics")
    error_summary: Dict[str, int] = Field(..., description="Error summary by operation")


class FileInfoResponse(BaseModel):
    """Response for file information."""

    success: bool = Field(..., description="Whether the request was successful")
    file_info: Dict[str, Any] = Field(..., description="File information")


# Unified Search API Models
class SearchRequest(BaseModel):
    """Request model for unified search."""

    query: str = Field(..., description="Search query", examples=["인공지능 기술 문서"], min_length=1)
    search_type: str = Field(
        "vector",
        description="Type of search to perform",
        examples=["vector", "text"]
    )
    limit: int = Field(default_factory=lambda: settings.default_search_limit, description="Maximum number of results", ge=1, le=1000)
    offset: int = Field(0, description="Number of results to skip", ge=0)
    score_threshold: float = Field(default_factory=lambda: settings.default_score_threshold, description="Minimum similarity score", ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    embedding_model: Optional[str] = Field(None, description="Embedding model to use")
    highlight: bool = Field(False, description="Whether to highlight search terms")
    rerank: bool = Field(False, description="Whether to apply reranking to results")
    rerank_top_k: Optional[int] = Field(None, description="Number of top results to consider for reranking")

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "인공지능 기술 문서",
                "search_type": "vector",
                "limit": 10,
                "filters": {
                    "file_type": ["pdf", "docx"],
                    "date_range": "2024-01-01 to 2024-12-31"
                }
            }
        }
    }





class SearchResult(BaseModel):
    """Individual search result."""

    id: str = Field(..., description="Document or chunk ID")
    score: float = Field(..., description="Relevance score")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    content: Optional[str] = Field(None, description="Document content or snippet")
    highlights: Optional[Dict[str, List[str]]] = Field(None, description="Highlighted text snippets")
    search_source: Optional[str] = Field(None, description="Source of the result (vector/text/both)")


class SearchResponse(BaseModel):
    """Response model for search operations."""

    success: bool = Field(..., description="Whether the search was successful")
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results found")
    search_type: str = Field(..., description="Type of search performed")
    query: str = Field(..., description="Original search query")
    search_time: float = Field(..., description="Time taken for search in seconds")
    backend: Optional[str] = Field(None, description="Backend used for search")
    error: Optional[str] = Field(None, description="Error message if search failed")








# Rerank Models
class RerankDocument(BaseModel):
    """Individual document for reranking."""

    id: Optional[str] = Field(None, description="Document or chunk ID")
    text: str = Field(..., description="Document text content")
    score: Optional[float] = Field(None, description="Original relevance score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "doc_123_chunk_1",
                "text": "인공지능 기술의 발전으로 자연어 처리 분야가 크게 발전했습니다.",
                "score": 0.85,
                "metadata": {
                    "file_name": "ai_report.pdf",
                    "chunk_index": 1
                }
            }
        }
    }


class RerankRequest(BaseModel):
    """Request model for document reranking."""

    query: str = Field(..., description="Search query for reranking")
    documents: List[RerankDocument] = Field(
        ...,
        description="List of documents to rerank",
        min_length=1,
        max_length=1000
    )
    top_k: Optional[int] = Field(
        None,
        description="Number of top results to return (None for all)",
        ge=1,
        le=1000
    )
    model: Optional[str] = Field(
        None,
        description="Rerank model to use (uses default if not specified)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "인공지능 기술 동향",
                "documents": [
                    {
                        "id": "doc1",
                        "text": "인공지능 기술의 최신 동향과 발전 방향",
                        "score": 0.8
                    },
                    {
                        "id": "doc2",
                        "text": "머신러닝과 딥러닝의 실제 적용 사례",
                        "score": 0.7
                    }
                ],
                "top_k": 10
            }
        }
    }


class RerankResult(BaseModel):
    """Individual reranked document result."""

    id: Optional[str] = Field(None, description="Document or chunk ID")
    text: str = Field(..., description="Document text content")
    score: float = Field(..., description="Rerank relevance score")
    rerank_score: float = Field(..., description="Cross-encoder rerank score")
    original_score: Optional[float] = Field(None, description="Original search score")
    rank_position: int = Field(..., description="Position in reranked results")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "doc1",
                "text": "인공지능 기술의 최신 동향과 발전 방향",
                "score": 0.92,
                "rerank_score": 0.92,
                "original_score": 0.8,
                "rank_position": 1,
                "metadata": {
                    "file_name": "ai_report.pdf"
                }
            }
        }
    }


class RerankResponse(BaseModel):
    """Response model for document reranking."""

    success: bool = Field(..., description="Whether reranking was successful")
    results: List[RerankResult] = Field(..., description="Reranked documents")
    query: str = Field(..., description="Original search query")
    total_count: int = Field(..., description="Total number of input documents")
    reranked_count: int = Field(..., description="Number of documents returned")
    processing_time: float = Field(..., description="Time taken for reranking")
    model_info: Dict[str, Any] = Field(..., description="Information about the rerank model used")
    rerank_applied: bool = Field(..., description="Whether reranking was actually applied")
    from_cache: Optional[bool] = Field(None, description="Whether result was served from cache")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "results": [
                    {
                        "id": "doc1",
                        "text": "인공지능 기술의 최신 동향과 발전 방향",
                        "score": 0.92,
                        "rerank_score": 0.92,
                        "original_score": 0.8,
                        "rank_position": 1
                    }
                ],
                "query": "인공지능 기술 동향",
                "total_count": 2,
                "reranked_count": 1,
                "processing_time": 0.045,
                "model_info": {
                    "model_name": "dragonkue/bge-reranker-v2-m3-ko",
                    "model_type": "cross_encoder"
                },
                "rerank_applied": True,
                "from_cache": False
            }
        }
    }
