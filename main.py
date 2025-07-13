"""Main FastAPI application for KURE embedding API."""

import logging
import time
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import settings
from models import (
    EmbeddingRequest, EmbeddingResponse, EmbeddingData,
    SimilarityRequest, SimilarityResponse,
    ModelsResponse, ModelInfo,
    HealthResponse, ErrorResponse,
    ChunkRequest, ChunkResponse, ChunkData,
    DocumentConversionRequest, DocumentConversionResponse, ConversionComparisonResponse,
    FileUploadResponse, DocumentProcessRequest, DocumentProcessResponse,
    VectorSearchRequest, VectorSearchResponse, QdrantStatsResponse,
    StorageStatsResponse, StorageFilesResponse, StorageCleanupResponse, FileInfoResponse,
    FileListResponse, FileInfo, DuplicateStatsResponse, DuplicateListResponse,
    SearchRequest, HybridSearchRequest, SearchResult, SearchResponse,
    HybridSearchResponse, SearchStatsResponse,
    RerankRequest, RerankResponse, RerankResult
)
from services import embedding_service, chunking_service
from services.marker_service import marker_service
from services.docling_service import docling_service
from services.file_upload_service import file_upload_service
from services.document_processing_service import document_processing_service
from services.database_service import database_service
from services.qdrant_service import qdrant_service
from services.search_service import search_service
from services.unified_search_service import unified_search_service
from services.storage_service import storage_service
from services.rerank_service import rerank_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting KURE API service...")
    start_time = time.time()

    try:
        # Load embedding model
        embedding_service.load_model(settings.default_model)

        # Initialize Qdrant (already done in service init, but verify connection)
        qdrant_health = qdrant_service.health_check()
        if qdrant_health.get("connected"):
            logger.info(f"✅ Qdrant connected: {qdrant_health.get('total_collections', 0)} collections")
        else:
            logger.warning(f"⚠️ Qdrant connection issue: {qdrant_health.get('error', 'Unknown')}")

        # Initialize unified search service
        logger.info("🔧 Initializing unified search service...")
        unified_init = await unified_search_service.initialize()
        if unified_init:
            logger.info("✅ Unified search service initialized successfully")
        else:
            logger.warning("⚠️ Unified search service initialization failed")

        # Initialize rerank service
        logger.info("🔧 Initializing rerank service...")
        rerank_init = await rerank_service.initialize()
        if rerank_init:
            logger.info("✅ Rerank service initialized successfully")
        else:
            logger.warning("⚠️ Rerank service initialization failed")

        startup_time = time.time() - start_time
        logger.info(f"Default model {settings.default_model} loaded successfully in {startup_time:.2f}s")
        logger.info("🚀 KURE API service is ready!")
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        raise  # This will prevent the application from starting

    yield  # Application runs here

    # Shutdown
    logger.info("Shutting down KURE API service...")
    try:
        # Clean up old uploaded files
        file_upload_service.cleanup_old_files(max_age_hours=24)

        # Clean up rerank service
        await rerank_service.cleanup()

        # Clean up memory
        embedding_service.cleanup_memory()
        logger.info("🛑 Resources cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "message": str(exc),
                "type": "invalid_request_error",
                "code": "invalid_input"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "Internal server error",
                "type": "internal_error",
                "code": "internal_error"
            }
        }
    )


# API Key dependency (OpenAI compatible)

async def verify_api_key(authorization: str = Header(None)):
    if settings.api_key:
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )

        # Extract Bearer token
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )

        token = authorization[7:]  # Remove "Bearer " prefix
        if token != settings.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

    return authorization


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        is_model_loaded=embedding_service.is_model_loaded(),
        version=settings.app_version
    )


@app.get("/memory")
async def memory_info():
    """Get memory usage information."""
    return embedding_service.get_memory_info()


@app.post("/memory/cleanup")
async def cleanup_memory():
    """Clean up GPU memory."""
    embedding_service.cleanup_memory()
    return {"status": "memory cleaned", "info": embedding_service.get_memory_info()}


@app.get("/models", response_model=ModelsResponse)
async def list_models():
    """List available models."""
    models = embedding_service.get_available_models()
    return ModelsResponse(
        object="list",
        data=[ModelInfo(**model) for model in models]
    )


@app.post("/embeddings", response_model=EmbeddingResponse)
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


@app.post("/similarity", response_model=SimilarityResponse)
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


@app.post("/v1/chunk", response_model=ChunkResponse)
async def chunk_text(
    request: ChunkRequest,
    authorization: str = Depends(verify_api_key)
):
    """Chunk text into smaller pieces for processing."""
    try:
        # Use request values or fall back to settings defaults
        strategy = request.strategy or settings.default_chunk_strategy
        chunk_size = request.chunk_size or settings.default_chunk_size
        overlap = request.overlap or settings.default_chunk_overlap
        language = request.language or settings.default_chunk_language

        # Validate overlap vs chunk_size after applying defaults
        if overlap >= chunk_size:
            raise ValueError("Overlap must be less than chunk_size")

        # Chunk the text
        chunks = chunking_service.chunk_text(
            text=request.text,
            strategy=strategy,
            chunk_size=chunk_size,
            overlap=overlap,
            language=language
        )

        # Convert to response format
        chunk_data = [
            ChunkData(
                text=chunk.text,
                index=i,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                token_count=chunk.token_count
            )
            for i, chunk in enumerate(chunks)
        ]

        total_tokens = sum(chunk.token_count for chunk in chunks)

        return ChunkResponse(
            object="list",
            data=chunk_data,
            total_chunks=len(chunks),
            strategy=strategy,  # Return actual strategy used
            original_length=len(request.text),
            total_tokens=total_tokens
        )

    except Exception as e:
        logger.error(f"Error chunking text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to chunk text: {str(e)}"
        )


@app.post("/v1/convert/marker", response_model=DocumentConversionResponse)
async def convert_with_marker(
    request: DocumentConversionRequest,
    authorization: str = Depends(verify_api_key)
):
    """Convert PDF to markdown using marker-pdf."""
    try:
        result = marker_service.convert_pdf_to_markdown(
            pdf_path=request.file_path,
            output_dir=request.output_dir,
            extract_images=request.extract_images
        )
        return DocumentConversionResponse(**result)
    except Exception as e:
        logger.error(f"Error in marker conversion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Marker conversion failed: {str(e)}"
        )


@app.post("/v1/convert/docling", response_model=DocumentConversionResponse)
async def convert_with_docling(
    request: DocumentConversionRequest,
    authorization: str = Depends(verify_api_key)
):
    """Convert PDF to markdown using docling."""
    try:
        result = docling_service.convert_pdf_to_markdown(
            pdf_path=request.file_path,
            output_dir=request.output_dir,
            extract_images=request.extract_images
        )
        return DocumentConversionResponse(**result)
    except Exception as e:
        logger.error(f"Error in docling conversion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Docling conversion failed: {str(e)}"
        )


@app.post("/v1/convert/compare", response_model=ConversionComparisonResponse)
async def compare_conversions(
    request: DocumentConversionRequest,
    authorization: str = Depends(verify_api_key)
):
    """Compare PDF conversion performance between marker and docling."""
    try:
        # Run both conversions
        marker_result = marker_service.convert_pdf_to_markdown(
            pdf_path=request.file_path,
            output_dir=request.output_dir,
            extract_images=request.extract_images
        )

        docling_result = docling_service.convert_pdf_to_markdown(
            pdf_path=request.file_path,
            output_dir=request.output_dir,
            extract_images=request.extract_images
        )

        # Check success status
        marker_success = marker_result.get('success', False)
        docling_success = docling_result.get('success', False)

        # Calculate comparison metrics
        speed_comparison = {
            "marker_time": marker_result.get('conversion_time', 0),
            "docling_time": docling_result.get('conversion_time', 0),
        }

        # Only compare speed if both conversions were successful
        if marker_success and docling_success:
            marker_time = marker_result.get('conversion_time', float('inf'))
            docling_time = docling_result.get('conversion_time', float('inf'))

            if marker_time < docling_time:
                speed_comparison["faster_library"] = "marker"
                speed_comparison["speed_ratio"] = docling_time / marker_time if marker_time > 0 else None
            else:
                speed_comparison["faster_library"] = "docling"
                speed_comparison["speed_ratio"] = marker_time / docling_time if docling_time > 0 else None
        elif marker_success and not docling_success:
            speed_comparison["faster_library"] = "marker"
            speed_comparison["speed_ratio"] = None
            speed_comparison["note"] = "Only marker succeeded"
        elif not marker_success and docling_success:
            speed_comparison["faster_library"] = "docling"
            speed_comparison["speed_ratio"] = None
            speed_comparison["note"] = "Only docling succeeded"
        else:
            speed_comparison["faster_library"] = None
            speed_comparison["speed_ratio"] = None
            speed_comparison["note"] = "Both conversions failed"

        comparison = {
            "speed_comparison": speed_comparison,
            "output_comparison": {
                "marker_markdown_length": marker_result.get('markdown_length', 0),
                "docling_markdown_length": docling_result.get('markdown_length', 0),
                "marker_images": marker_result.get('images_count', 0),
                "docling_images": docling_result.get('images_count', 0)
            },
            "resource_usage": {
                "marker_gpu_memory": marker_result.get('gpu_memory_used_gb'),
                "docling_gpu_memory": docling_result.get('gpu_memory_used_gb')
            }
        }

        return ConversionComparisonResponse(
            marker_result=DocumentConversionResponse(**marker_result),
            docling_result=DocumentConversionResponse(**docling_result),
            comparison=comparison
        )

    except Exception as e:
        logger.error(f"Error in conversion comparison: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion comparison failed: {str(e)}"
        )


@app.post("/v1/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    authorization: str = Depends(verify_api_key)
):
    """Upload a file for processing."""
    try:
        result = await file_upload_service.upload_file(file)
        return FileUploadResponse(**result)
    except Exception as e:
        logger.error(f"Error in file upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@app.post("/v1/process", response_model=DocumentProcessResponse)
async def process_document(
    request: DocumentProcessRequest,
    authorization: str = Depends(verify_api_key)
):
    """Process uploaded document through the full pipeline."""
    try:
        result = await document_processing_service.process_document(
            file_id=request.file_id,
            conversion_method=request.conversion_method,
            extract_images=request.extract_images,
            chunk_strategy=request.chunk_strategy,
            chunk_size=request.chunk_size,
            overlap=request.overlap,
            generate_embeddings=request.generate_embeddings,
            embedding_model=request.embedding_model
        )
        return DocumentProcessResponse(**result)
    except Exception as e:
        logger.error(f"Error in document processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


@app.get("/v1/documents")
async def list_documents(
    page: int = 1,
    page_size: int = 100,
    authorization: str = Depends(verify_api_key)
):
    """List all processed documents with pagination."""
    try:
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 1000:
            page_size = 100

        result = document_processing_service.list_documents(page, page_size)
        return result
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@app.get("/v1/documents/{document_id}")
async def get_document(
    document_id: str,
    authorization: str = Depends(verify_api_key)
):
    """Get processed document by ID."""
    try:
        document = document_processing_service.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@app.get("/v1/files", response_model=FileListResponse)
async def list_files(
    page: int = 1,
    page_size: int = 100,
    authorization: str = Depends(verify_api_key)
):
    """List uploaded files with duplicate information."""
    try:
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be >= 1"
            )

        if page_size < 1 or page_size > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 1000"
            )

        result = database_service.list_files(page=page, page_size=page_size)
        return FileListResponse(
            success=True,
            **result
        )
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )


@app.delete("/v1/files/{file_id}")
async def delete_file(
    file_id: str,
    authorization: str = Depends(verify_api_key)
):
    """Delete uploaded file."""
    try:
        success = file_upload_service.delete_file(file_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_id}"
            )
        return {"success": True, "message": f"File {file_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@app.get("/v1/duplicates/stats", response_model=DuplicateStatsResponse)
async def get_duplicate_stats(
    authorization: str = Depends(verify_api_key)
):
    """Get statistics about duplicate files."""
    try:
        stats = database_service.get_duplicate_stats()
        return DuplicateStatsResponse(
            success=True,
            **stats
        )
    except Exception as e:
        logger.error(f"Error getting duplicate stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get duplicate stats: {str(e)}"
        )


@app.get("/v1/duplicates", response_model=DuplicateListResponse)
async def list_duplicate_groups(
    page: int = 1,
    page_size: int = 50,
    authorization: str = Depends(verify_api_key)
):
    """List groups of duplicate files."""
    try:
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page number must be >= 1"
            )

        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )

        result = database_service.list_duplicate_groups(page=page, page_size=page_size)
        return DuplicateListResponse(
            success=True,
            **result
        )
    except Exception as e:
        logger.error(f"Error listing duplicate groups: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list duplicate groups: {str(e)}"
        )


@app.get("/v1/stats")
async def get_database_stats(authorization: str = Depends(verify_api_key)):
    """Get database statistics."""
    try:
        stats = database_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database stats: {str(e)}"
        )


@app.post("/v1/search", response_model=VectorSearchResponse)
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


@app.get("/v1/qdrant/stats")
async def get_qdrant_stats(authorization: str = Depends(verify_api_key)):
    """Get Qdrant collection statistics."""
    try:
        stats = qdrant_service.get_collection_stats()
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Qdrant service unavailable"
            )
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Qdrant stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Qdrant stats: {str(e)}"
        )


@app.get("/v1/qdrant/health")
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


@app.get("/v1/search/stats")
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


# Unified Search API Endpoints
@app.post("/v1/search/vector", response_model=SearchResponse)
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

        # Convert to SearchResponse format
        search_results = []
        for item in result.get("results", []):
            metadata = item.get("metadata", {})
            # Qdrant stores text in metadata.text, not metadata.content
            content = metadata.get("text", metadata.get("content", ""))
            search_results.append(SearchResult(
                id=str(item.get("id", "")),
                score=item.get("score", 0.0),
                metadata=metadata,
                content=content,
                search_source="vector"
            ))

        return SearchResponse(
            success=True,
            results=search_results,
            total_results=result.get("total_results", 0),
            search_type="vector",
            query=request.query,
            search_time=result.get("search_time", 0.0),
            backend=result.get("backend", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified vector search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {str(e)}"
        )


@app.post("/v1/search/text", response_model=SearchResponse)
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
            offset=request.offset,
            filters=request.filters,
            highlight=request.highlight
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Text search failed")
            )

        # Convert to SearchResponse format
        search_results = []
        for item in result.get("results", []):
            search_results.append(SearchResult(
                id=str(item.get("id", "")),
                score=1.0,  # Text search might not have explicit scores
                metadata=item,
                content=item.get("content", ""),
                highlights=item.get("_formatted", {}) if request.highlight else None,
                search_source="text"
            ))

        return SearchResponse(
            success=True,
            results=search_results,
            total_results=result.get("total", 0),
            search_type="text",
            query=request.query,
            search_time=result.get("search_time", 0.0),
            backend=result.get("backend", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in unified text search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text search failed: {str(e)}"
        )


@app.post("/v1/search/hybrid", response_model=HybridSearchResponse)
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

        # Convert to HybridSearchResponse format
        search_results = []
        for item in result.get("results", []):
            metadata = item.get("metadata", {})
            # Qdrant stores text in metadata.text, not metadata.content
            content = metadata.get("text", metadata.get("content", item.get("content", "")))
            search_results.append(SearchResult(
                id=str(item.get("id", "")),
                score=item.get("hybrid_score", item.get("score", 0.0)),
                metadata=metadata,
                content=content,
                highlights=item.get("highlights"),
                search_source=item.get("search_source", "hybrid")
            ))

        return HybridSearchResponse(
            success=True,
            results=search_results,
            total_results=result.get("total_results", 0),
            search_type="hybrid",
            query=request.query,
            search_time=result.get("search_time", 0.0),
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


@app.get("/v1/search/unified/stats", response_model=SearchStatsResponse)
async def get_unified_search_stats(authorization: str = Depends(verify_api_key)):
    """Get unified search service statistics and backend information."""
    try:
        if not unified_search_service.is_initialized:
            return SearchStatsResponse(
                success=False,
                unified_search={"initialized": False, "error": "Service not initialized"},
                vector_backend={},
                text_backend={},
                available_backends={"vector": [], "text": []}
            )

        stats = unified_search_service.get_stats()
        health = await unified_search_service.health_check()

        # Get available backends
        from services.search_factory import SearchBackendFactory
        available_backends = {
            "vector": SearchBackendFactory.get_available_vector_backends(),
            "text": SearchBackendFactory.get_available_text_backends()
        }

        return SearchStatsResponse(
            success=True,
            unified_search=stats.get("unified_search", {}),
            vector_backend=stats.get("vector_backend", {}),
            text_backend=stats.get("text_backend", {}),
            available_backends=available_backends
        )

    except Exception as e:
        logger.error(f"Error getting unified search stats: {str(e)}")
        return SearchStatsResponse(
            success=False,
            unified_search={"error": str(e)},
            vector_backend={},
            text_backend={},
            available_backends={"vector": [], "text": []}
        )


@app.get("/v1/search/unified/health")
async def get_unified_search_health(authorization: str = Depends(verify_api_key)):
    """Check unified search service health."""
    try:
        health = await unified_search_service.health_check()
        return health
    except Exception as e:
        logger.error(f"Error checking unified search health: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "initialized": unified_search_service.is_initialized
        }


# Storage Management Endpoints

@app.get("/v1/storage/stats", response_model=StorageStatsResponse)
async def get_storage_stats(authorization: str = Depends(verify_api_key)):
    """Get storage usage statistics."""
    try:
        stats = storage_service.get_storage_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting storage stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage stats: {str(e)}"
        )


@app.get("/v1/storage/files/{directory_type}", response_model=StorageFilesResponse)
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


@app.post("/v1/storage/cleanup", response_model=StorageCleanupResponse)
async def cleanup_temp_files(
    max_age_hours: int = 24,
    authorization: str = Depends(verify_api_key)
):
    """Clean up temporary files older than specified hours."""
    try:
        deleted_count = storage_service.cleanup_temp_files(max_age_hours)
        return {
            "success": True,
            "deleted_count": deleted_count,
            "max_age_hours": max_age_hours
        }
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup temp files: {str(e)}"
        )


@app.get("/v1/storage/file-info", response_model=FileInfoResponse)
async def get_file_info(
    file_path: str,
    authorization: str = Depends(verify_api_key)
):
    """Get information about a specific file."""
    try:
        file_info = storage_service.get_file_info(file_path)
        return {
            "success": True,
            "file_info": file_info
        }
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file info: {str(e)}"
        )


# Rerank API Endpoints
@app.post("/v1/rerank", response_model=RerankResponse)
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

        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Reranking failed")
            )

        # Convert results to RerankResult format
        rerank_results = []
        for doc in result["documents"]:
            rerank_result = RerankResult(
                id=doc.get("id"),
                text=doc["text"],
                score=doc["score"],
                rerank_score=doc.get("rerank_score", doc["score"]),
                original_score=doc.get("original_score"),
                rank_position=doc.get("final_rank", doc.get("rank_position", 1)),
                metadata=doc.get("metadata", {})
            )
            rerank_results.append(rerank_result)

        return RerankResponse(
            success=True,
            results=rerank_results,
            query=request.query,
            total_count=result.get("original_count", len(request.documents)),
            reranked_count=result.get("reranked_count", len(rerank_results)),
            processing_time=result.get("processing_time", 0.0),
            model_info=result.get("model_info", {}),
            rerank_applied=result.get("rerank_applied", True),
            from_cache=result.get("from_cache", False)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in rerank endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rerank operation failed: {str(e)}"
        )


@app.get("/v1/rerank/models")
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


@app.get("/v1/rerank/stats")
async def get_rerank_stats(authorization: str = Depends(verify_api_key)):
    """Get rerank service statistics and cache information."""
    try:
        model_info = rerank_service.get_model_info()
        cache_stats = rerank_service.get_cache_stats()

        return {
            "success": True,
            "enabled": rerank_service.is_enabled(),
            "model_info": model_info,
            "cache_stats": cache_stats,
            "settings": {
                "rerank_enabled": getattr(settings, 'rerank_enabled', True),
                "rerank_model": getattr(settings, 'rerank_model', 'dragonkue/bge-reranker-v2-m3-ko'),
                "rerank_top_k": getattr(settings, 'rerank_top_k', 100),
                "rerank_batch_size": getattr(settings, 'rerank_batch_size', 32)
            }
        }

    except Exception as e:
        logger.error(f"Error getting rerank stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rerank stats: {str(e)}"
        )


@app.post("/v1/rerank/cache/clear")
async def clear_rerank_cache(authorization: str = Depends(verify_api_key)):
    """Clear the rerank cache."""
    try:
        rerank_service.clear_cache()
        return {
            "success": True,
            "message": "Rerank cache cleared successfully"
        }

    except Exception as e:
        logger.error(f"Error clearing rerank cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear rerank cache: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level.lower()
    )
