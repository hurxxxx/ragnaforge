"""Main FastAPI application for KURE embedding API."""

import logging
import time
import tempfile
import os
from typing import List
from fastapi import FastAPI, HTTPException, Depends, status, Header, UploadFile, File, Form
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
    DocumentConvertRequest, DocumentConvertResponse
)
from services import embedding_service, chunking_service
from services.document_conversion_service import document_conversion_service

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


@app.post("/v1/convert", response_model=DocumentConvertResponse)
async def convert_document(
    file: UploadFile = File(...),
    output_format: str = Form("markdown"),
    extract_images: bool = Form(True),
    use_llm: bool = Form(False),
    authorization: str = Depends(verify_api_key)
):
    """Convert document to markdown/json/html format with image extraction."""
    try:
        # Validate file format
        if not document_conversion_service.is_supported_format(file.filename):
            supported_formats = document_conversion_service.get_supported_formats()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Supported formats: {supported_formats}"
            )

        # Validate output format
        if output_format not in ["markdown", "json", "html"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Output format must be one of: markdown, json, html"
            )

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Convert document
            result = document_conversion_service.convert_document(
                file_path=temp_file_path,
                output_format=output_format,
                extract_images=extract_images,
                use_llm=use_llm
            )

            return DocumentConvertResponse(**result)

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert document: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level.lower()
    )
