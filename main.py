"""Main FastAPI application for KURE embedding API."""

import logging
import time
from typing import List
from fastapi import FastAPI, HTTPException, Depends, status, Header
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
    DocumentConversionRequest, DocumentConversionResponse, ConversionComparisonResponse
)
from services import embedding_service, chunking_service
from services.marker_service import marker_service
from services.docling_service import docling_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
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


@app.on_event("startup")
async def startup_event():
    """Load default model on startup."""
    logger.info("Starting KURE API service...")
    try:
        embedding_service.load_model(settings.default_model)
        logger.info(f"Default model {settings.default_model} loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load default model: {str(e)}")


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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level.lower()
    )
