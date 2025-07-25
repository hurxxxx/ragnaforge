"""Unified document conversion API router."""

import os
import base64
import logging
import tempfile
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from models import (
    UnifiedConversionResponse, ConversionEngine, ImageInfo,
    SupportedFileType
)
from services.marker_service import marker_service
from services.docling_service import docling_service
from routers.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/convert", tags=["Document Conversion"])


@router.post("/", response_model=UnifiedConversionResponse)
async def convert_document(
    file: UploadFile = File(..., description="Document file to convert"),
    engine: ConversionEngine = Form(ConversionEngine.MARKER, description="Conversion engine to use"),
    extract_images: bool = Form(True, description="Whether to extract images (marker only)"),
    include_image_data: bool = Form(False, description="Include base64 image data in response"),
    authorization: str = Depends(verify_api_key)
):
    """
    Convert document to markdown using Marker or Docling.
    
    This unified API endpoint provides document conversion with the following features:
    
    **Supported Formats:**
    - PDF (both engines)
    - DOCX, PPTX, XLSX (Docling only)
    
    **Engine Selection:**
    - `marker`: Fast, high-quality PDF conversion with image extraction
    - `docling`: Multi-format support (PDF, Office documents)
    - `auto`: Automatic selection based on file type
    
    **Response includes:**
    - Converted markdown content
    - Document metadata
    - Processing statistics
    - Extracted images (marker only)
    - Error handling and warnings
    
    **Authentication:**
    Requires Bearer token in Authorization header.
    """
    
    temp_file_path = None
    temp_dir = None
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        # Get file extension and validate
        file_extension = Path(file.filename).suffix.lower()
        supported_extensions = {'.pdf', '.docx', '.pptx', '.xlsx'}
        
        if file_extension not in supported_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_extension}. Supported: {', '.join(supported_extensions)}"
            )
        
        # Auto-select engine based on file type
        if engine == ConversionEngine.AUTO:
            if file_extension == '.pdf':
                engine = ConversionEngine.MARKER
            else:
                engine = ConversionEngine.DOCLING
        
        # Validate engine compatibility
        if engine == ConversionEngine.MARKER and file_extension != '.pdf':
            logger.warning(f"Marker doesn't support {file_extension}, switching to Docling")
            engine = ConversionEngine.DOCLING
        
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = Path(temp_dir) / file.filename
        
        # Save uploaded file
        logger.info(f"Saving uploaded file: {file.filename} ({file_extension})")
        content = await file.read()
        
        with open(temp_file_path, 'wb') as f:
            f.write(content)
        
        file_size_mb = len(content) / (1024 * 1024)
        logger.info(f"File saved: {file_size_mb:.2f}MB")
        
        # Perform conversion
        logger.info(f"Starting conversion with {engine.value} engine")
        
        if engine == ConversionEngine.MARKER:
            result = await _convert_with_marker(
                temp_file_path, temp_dir, extract_images, include_image_data
            )
        else:  # DOCLING
            result = await _convert_with_docling(
                temp_file_path, temp_dir, file_extension
            )
        
        # Add common file info
        result["file_info"] = {
            "filename": file.filename,
            "size_mb": file_size_mb,
            "format": file_extension,
            "content_type": file.content_type
        }
        
        logger.info(f"Conversion completed successfully with {engine.value}")
        return UnifiedConversionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion failed: {str(e)}"
        )
    
    finally:
        # Cleanup temporary files
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {e}")
        
        if temp_dir and Path(temp_dir).exists():
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {e}")


async def _convert_with_marker(
    file_path: Path, 
    output_dir: str, 
    extract_images: bool,
    include_image_data: bool
) -> dict:
    """Convert document using Marker."""
    
    result = marker_service.convert_pdf_to_markdown(
        pdf_path=str(file_path),
        output_dir=output_dir,
        extract_images=extract_images
    )
    
    if not result.get("success"):
        raise Exception(result.get("error", "Marker conversion failed"))
    
    # Process images if available
    images_info = []
    if extract_images and result.get("images_count", 0) > 0:
        images_info = await _process_marker_images(
            output_dir, include_image_data
        )
    
    return {
        "success": True,
        "engine_used": "marker",
        "conversion_time": result.get("conversion_time", 0),
        "markdown_content": result.get("markdown", ""),
        "content_length": result.get("markdown_length", 0),
        "document_metadata": result.get("metadata", {}),
        "images": images_info,
        "images_count": len(images_info),
        "processing_stats": {
            "gpu_memory_used_gb": result.get("gpu_memory_used_gb"),
            "library": result.get("library"),
            "saved_files": result.get("saved_files", [])
        },
        "error": None,
        "warnings": []
    }


async def _convert_with_docling(
    file_path: Path, 
    output_dir: str,
    file_extension: str
) -> dict:
    """Convert document using Docling."""
    
    if file_extension == '.pdf':
        result = docling_service.convert_pdf_to_markdown(
            pdf_path=str(file_path),
            output_dir=output_dir,
            extract_images=False  # Docling image extraction is limited
        )
    else:
        result = docling_service.convert_office_to_markdown(
            file_path=str(file_path),
            output_dir=output_dir
        )
    
    if not result.get("success"):
        raise Exception(result.get("error", "Docling conversion failed"))
    
    return {
        "success": True,
        "engine_used": "docling",
        "conversion_time": result.get("conversion_time", 0),
        "markdown_content": result.get("markdown", ""),
        "content_length": result.get("markdown_length", 0),
        "document_metadata": result.get("metadata", {}),
        "images": [],  # Docling doesn't provide detailed image info
        "images_count": result.get("images_count", 0),
        "processing_stats": {
            "gpu_memory_used_gb": result.get("gpu_memory_used_gb"),
            "library": result.get("library"),
            "saved_files": result.get("saved_files", []),
            "file_type": result.get("file_type")
        },
        "error": None,
        "warnings": []
    }


async def _process_marker_images(
    output_dir: str,
    include_image_data: bool
) -> List[dict]:
    """Process images extracted by Marker."""
    
    images_info = []
    output_path = Path(output_dir)
    
    # Look for image files in output directory
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
    
    for image_file in output_path.glob("*"):
        if image_file.suffix.lower() in image_extensions:
            try:
                image_info = {
                    "filename": image_file.name,
                    "format": image_file.suffix.lower()[1:],  # Remove dot
                    "size_bytes": image_file.stat().st_size,
                    "dimensions": None,  # Could add PIL to get dimensions
                    "page_number": None,  # Could extract from filename pattern
                    "base64_data": None
                }
                
                # Include base64 data if requested
                if include_image_data:
                    with open(image_file, 'rb') as f:
                        image_data = f.read()
                        image_info["base64_data"] = base64.b64encode(image_data).decode('utf-8')
                
                images_info.append(image_info)
                
            except Exception as e:
                logger.warning(f"Failed to process image {image_file}: {e}")
    
    return images_info


@router.get("/engines")
async def list_conversion_engines():
    """
    List available conversion engines and their capabilities.
    
    Returns information about supported engines, file formats, and features.
    """
    
    return {
        "engines": {
            "marker": {
                "name": "Marker",
                "description": "Fast, high-quality PDF conversion with image extraction",
                "supported_formats": [".pdf"],
                "features": [
                    "High-quality text extraction",
                    "Image extraction",
                    "Table preservation",
                    "Mathematical formula support",
                    "GPU acceleration"
                ],
                "best_for": "PDF documents, especially scientific papers and books"
            },
            "docling": {
                "name": "Docling",
                "description": "Multi-format document converter",
                "supported_formats": [".pdf", ".docx", ".pptx", ".xlsx"],
                "features": [
                    "Multi-format support",
                    "Office document native support",
                    "Metadata extraction",
                    "Layout preservation",
                    "GPU acceleration"
                ],
                "best_for": "Office documents and mixed document types"
            }
        },
        "auto_selection": {
            "pdf": "marker",
            "docx": "docling",
            "pptx": "docling", 
            "xlsx": "docling"
        }
    }


@router.get("/health")
async def conversion_health():
    """Check conversion services health."""
    
    marker_info = marker_service.get_info()
    docling_info = docling_service.get_info()
    
    return {
        "status": "healthy",
        "services": {
            "marker": marker_info,
            "docling": docling_info
        },
        "supported_formats": [".pdf", ".docx", ".pptx", ".xlsx"]
    }
