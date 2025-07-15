"""File upload and management API routes."""

import logging
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from typing import Optional

from models import (
    FileUploadResponse, DocumentProcessRequest, DocumentProcessResponse,
    FileListResponse, FileInfo, FileInfoResponse,
    DocumentConversionRequest, DocumentConversionResponse, ConversionComparisonResponse
)
from services.file_upload_service import file_upload_service
from services.document_processing_service import document_processing_service
from services.database_service import database_service
from services.marker_service import marker_service
from services.docling_service import docling_service
from routers.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    authorization: str = Depends(verify_api_key)
):
    """Upload a file for processing."""
    try:
        result = await file_upload_service.upload_file(file)

        # Check if upload failed due to validation (e.g., empty file)
        if not result.get("success", True):
            error_msg = result.get("error", "Upload failed")
            if "Empty files are not allowed" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )

        return FileUploadResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in file upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )


@router.post("/upload_and_process", response_model=DocumentProcessResponse)
async def upload_and_process_document(
    file: UploadFile = File(...),
    conversion_method: str = "auto",
    extract_images: bool = False,
    chunk_strategy: Optional[str] = None,
    chunk_size: Optional[int] = None,
    overlap: Optional[int] = None,
    generate_embeddings: bool = True,
    embedding_model: Optional[str] = None,
    authorization: str = Depends(verify_api_key)
):
    """Upload a file and process it through the full pipeline in one request.

    This endpoint combines file upload and document processing into a single API call:
    1. Upload and validate the file
    2. Convert document to markdown (using marker or docling)
    3. Split text into chunks
    4. Generate embeddings
    5. Store in vector and text search databases

    Returns the complete processing results including file info, chunks, and storage status.
    """
    try:
        # Step 1: Upload file
        logger.info(f"📤 Starting upload and process for file: {file.filename}")
        upload_result = await file_upload_service.upload_file(file)

        # Check if upload failed
        if not upload_result.get("success", True):
            error_msg = upload_result.get("error", "Upload failed")
            if "Empty files are not allowed" in error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

        file_id = upload_result.get("file_id")
        logger.info(f"✅ File uploaded successfully: {file_id}")

        # Step 2: Process document through full pipeline
        logger.info(f"🔄 Starting document processing for file: {file_id}")
        result = await document_processing_service.process_document(
            file_id=file_id,
            conversion_method=conversion_method,
            extract_images=extract_images,
            chunk_strategy=chunk_strategy,
            chunk_size=chunk_size,
            overlap=overlap,
            generate_embeddings=generate_embeddings,
            embedding_model=embedding_model
        )

        # Add upload info to result
        result["upload_info"] = {
            "file_id": file_id,
            "filename": upload_result.get("filename"),
            "file_size": upload_result.get("file_size"),
            "upload_time": upload_result.get("upload_time"),
            "storage_path": upload_result.get("storage_path")
        }

        logger.info(f"🎉 Upload and process completed successfully for: {file.filename}")
        return DocumentProcessResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload and process: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload and process failed: {str(e)}"
        )


@router.post("/process", response_model=DocumentProcessResponse)
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


@router.get("/files", response_model=FileListResponse)
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


@router.get("/files/{file_id}", response_model=FileInfoResponse)
async def get_file_info(
    file_id: str,
    authorization: str = Depends(verify_api_key)
):
    """Get detailed information about a specific file."""
    try:
        file_info = database_service.get_file_info(file_id)
        if not file_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_id}"
            )
        
        return FileInfoResponse(
            success=True,
            file=FileInfo(**file_info)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file info: {str(e)}"
        )


@router.post("/convert/marker", response_model=DocumentConversionResponse)
async def convert_with_marker(
    request: DocumentConversionRequest,
    authorization: str = Depends(verify_api_key)
):
    """Convert PDF to markdown using Marker."""
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


@router.post("/convert/docling", response_model=DocumentConversionResponse)
async def convert_with_docling(
    request: DocumentConversionRequest,
    authorization: str = Depends(verify_api_key)
):
    """Convert PDF to markdown using Docling."""
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


@router.post("/convert/compare", response_model=ConversionComparisonResponse)
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

        # Compare results
        comparison = {
            "marker": marker_result,
            "docling": docling_result,
            "comparison": {
                "marker_faster": marker_result["processing_time"] < docling_result["processing_time"],
                "time_difference": abs(marker_result["processing_time"] - docling_result["processing_time"]),
                "marker_larger_output": len(marker_result.get("content", "")) > len(docling_result.get("content", "")),
                "size_difference": abs(len(marker_result.get("content", "")) - len(docling_result.get("content", "")))
            }
        }

        return ConversionComparisonResponse(
            success=True,
            **comparison
        )

    except Exception as e:
        logger.error(f"Error in conversion comparison: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion comparison failed: {str(e)}"
        )
