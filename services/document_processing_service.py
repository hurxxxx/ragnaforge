"""Document processing service for uploaded files."""

import time
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from models import SupportedFileType
from services.file_upload_service import file_upload_service
from services.marker_service import marker_service
from services.docling_service import docling_service
from services import chunking_service, embedding_service
from config import settings

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """Service for processing uploaded documents."""

    def __init__(self):
        logger.info("Document processing service initialized")
    
    def _choose_conversion_method(self, file_type: SupportedFileType, method: str = "auto") -> str:
        """Choose the best conversion method for the file type."""
        if method in ["marker", "docling"]:
            return method
        
        # Auto selection logic
        if file_type == SupportedFileType.PDF:
            return "docling"  # Docling is generally faster for PDFs
        elif file_type in [SupportedFileType.DOCX, SupportedFileType.PPTX]:
            return "docling"  # Docling supports these formats
        else:
            return "marker"  # Fallback to marker
    
    def _read_text_file(self, file_path: Path) -> str:
        """Read content from text files."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    async def _convert_document(self, file_path: Path, file_type: SupportedFileType, 
                               method: str, extract_images: bool = False) -> Dict:
        """Convert document to markdown."""
        try:
            if file_type in [SupportedFileType.TXT, SupportedFileType.MD]:
                # For text files, just read the content
                content = self._read_text_file(file_path)
                return {
                    "success": True,
                    "markdown_content": content,
                    "markdown_length": len(content),
                    "conversion_time": 0.1,
                    "method_used": "direct_read"
                }
            
            elif file_type == SupportedFileType.PDF:
                if method == "marker":
                    result = marker_service.convert_pdf_to_markdown(
                        pdf_path=str(file_path),
                        output_dir="temp_processing",
                        extract_images=extract_images
                    )
                else:  # docling
                    result = docling_service.convert_pdf_to_markdown(
                        pdf_path=str(file_path),
                        output_dir="temp_processing",
                        extract_images=extract_images
                    )
                
                if result.get("success"):
                    return {
                        "success": True,
                        "markdown_content": result.get("markdown", ""),
                        "markdown_length": result.get("markdown_length", 0),
                        "conversion_time": result.get("conversion_time", 0),
                        "method_used": method
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Conversion failed"),
                        "method_used": method
                    }
            
            elif file_type in [SupportedFileType.DOCX, SupportedFileType.PPTX]:
                # Use docling for Office documents
                result = docling_service.convert_pdf_to_markdown(
                    pdf_path=str(file_path),
                    output_dir="temp_processing",
                    extract_images=extract_images
                )
                
                if result.get("success"):
                    return {
                        "success": True,
                        "markdown_content": result.get("markdown", ""),
                        "markdown_length": result.get("markdown_length", 0),
                        "conversion_time": result.get("conversion_time", 0),
                        "method_used": "docling"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", "Conversion failed"),
                        "method_used": "docling"
                    }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type for conversion: {file_type}",
                    "method_used": method
                }
                
        except Exception as e:
            logger.error(f"Error converting document: {str(e)}")
            return {
                "success": False,
                "error": f"Conversion error: {str(e)}",
                "method_used": method
            }
    
    def _chunk_text(self, text: str, strategy: str, chunk_size: int, overlap: int) -> List[Dict]:
        """Chunk text into smaller pieces."""
        try:
            chunks = chunking_service.chunk_text(
                text=text,
                strategy=strategy,
                chunk_size=chunk_size,
                overlap=overlap,
                language="auto"
            )
            
            return [
                {
                    "text": chunk.text,
                    "index": i,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "token_count": chunk.token_count
                }
                for i, chunk in enumerate(chunks)
            ]
            
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            return []
    
    def _generate_embeddings(self, chunks: List[Dict], model: str) -> bool:
        """Generate embeddings for text chunks."""
        try:
            texts = [chunk["text"] for chunk in chunks]
            embeddings = embedding_service.encode_texts(texts, model)
            
            # Add embeddings to chunks
            for i, chunk in enumerate(chunks):
                chunk["embedding"] = embeddings[i].tolist()
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return False
    
    async def process_document(self, file_id: str, conversion_method: str = "auto",
                              extract_images: bool = False, chunk_strategy: Optional[str] = None,
                              chunk_size: Optional[int] = None, overlap: Optional[int] = None,
                              generate_embeddings: bool = True, embedding_model: Optional[str] = None) -> Dict:
        """Process uploaded document through the full pipeline."""
        start_time = time.time()
        
        try:
            # Get file info
            file_info = file_upload_service.get_file_info(file_id)
            if not file_info:
                return {
                    "success": False,
                    "error": f"File not found: {file_id}",
                    "processing_time": time.time() - start_time
                }
            
            file_path = Path(file_info["temp_path"])
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found on disk: {file_path}",
                    "processing_time": time.time() - start_time
                }
            
            # Set defaults
            chunk_strategy = chunk_strategy or settings.default_chunk_strategy
            chunk_size = chunk_size or settings.default_chunk_size
            overlap = overlap or settings.default_chunk_overlap
            embedding_model = embedding_model or settings.default_model
            
            # Choose conversion method
            file_type = file_info["file_type"]
            method = self._choose_conversion_method(file_type, conversion_method)
            
            # Convert document
            conversion_result = await self._convert_document(
                file_path, file_type, method, extract_images
            )
            
            if not conversion_result.get("success"):
                return {
                    "success": False,
                    "error": conversion_result.get("error", "Conversion failed"),
                    "processing_time": time.time() - start_time
                }
            
            markdown_content = conversion_result["markdown_content"]
            
            # Chunk text
            chunks = self._chunk_text(markdown_content, chunk_strategy, chunk_size, overlap)
            
            # Generate embeddings if requested
            embeddings_generated = False
            if generate_embeddings and chunks:
                embeddings_generated = self._generate_embeddings(chunks, embedding_model)
            
            # Generate document ID
            document_id = str(uuid.uuid4())

            # Store processed content using storage service
            from services.storage_service import storage_service

            # Store markdown content
            markdown_storage = storage_service.store_processed_content(
                file_id=file_id,
                content_type="markdown",
                content=markdown_content,
                filename=f"{document_id}_converted.md"
            )

            # Store chunks as JSON
            import json
            chunks_json = json.dumps(chunks, ensure_ascii=False, indent=2)
            chunks_storage = storage_service.store_processed_content(
                file_id=file_id,
                content_type="chunks",
                content=chunks_json,
                filename=f"{document_id}_chunks.json"
            )

            # Store processed document metadata
            processed_doc = {
                "document_id": document_id,
                "file_id": file_id,
                "filename": file_info["filename"],
                "file_type": file_type,
                "conversion_method": method,
                "conversion_time": conversion_result["conversion_time"],
                "markdown_content": markdown_content,
                "markdown_storage_path": markdown_storage["storage_path"],
                "chunks": chunks,
                "chunks_storage_path": chunks_storage["storage_path"],
                "embeddings_generated": embeddings_generated,
                "processing_time": time.time() - start_time,
                "created_at": time.time()
            }

            # Store in database
            from services.database_service import database_service
            database_service.store_document(processed_doc)

            # Store in unified search service if embeddings were generated
            if embeddings_generated and chunks:
                try:
                    from services.unified_search_service import unified_search_service

                    # Prepare documents for unified search service
                    documents = []
                    for i, chunk in enumerate(chunks):
                        # 청킹 서비스에서 text 필드에 텍스트를 저장하므로 이를 content로 매핑
                        chunk_text = chunk.get("text", "")
                        doc = {
                            "id": f"{document_id}_chunk_{i}",
                            "document_id": document_id,
                            "embedding": chunk.get("embedding"),
                            "content": chunk_text,  # text 필드를 content로 매핑
                            "title": file_info["filename"],
                            "file_name": file_info["filename"],
                            "file_type": file_type,
                            "chunk_index": i,
                            "file_size": file_info.get("size", 0),
                            "created_at": time.time(),
                            "metadata": {
                                "filename": file_info["filename"],
                                "file_type": file_type,
                                "conversion_method": method,
                                "created_at": time.time(),
                                "embedding_model": embedding_model,
                                "document_id": document_id,
                                "chunk_index": i,
                                "text": chunk_text,  # Qdrant용 text 필드
                                "content": chunk_text  # MeiliSearch용 content 필드
                            }
                        }
                        documents.append(doc)

                    # Store in unified search service (both vector and text backends)
                    unified_success = await unified_search_service.store_documents(documents)

                    if unified_success:
                        logger.info(f"Document chunks stored in unified search service: {document_id}")
                    else:
                        logger.warning(f"Failed to store chunks in unified search service: {document_id}")

                except Exception as e:
                    logger.error(f"Error storing chunks in unified search service: {str(e)}")
                    # Don't fail the whole process if unified search fails
            
            logger.info(f"Document processed successfully: {file_info['filename']} -> {document_id}")
            
            return {
                "success": True,
                "file_id": file_id,
                "document_id": document_id,
                "filename": file_info["filename"],
                "conversion_method": method,
                "conversion_time": conversion_result["conversion_time"],
                "markdown_content": markdown_content,
                "markdown_length": len(markdown_content),
                "total_chunks": len(chunks),
                "chunks": chunks,
                "embeddings_generated": embeddings_generated,
                "processing_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Error processing document {file_id}: {str(e)}")
            return {
                "success": False,
                "error": f"Processing failed: {str(e)}",
                "processing_time": time.time() - start_time
            }
    
    def get_document(self, document_id: str) -> Optional[Dict]:
        """Get processed document by ID."""
        from services.database_service import database_service
        return database_service.get_document(document_id)

    def list_documents(self, page: int = 1, page_size: int = 100) -> Dict:
        """List all processed documents with pagination."""
        from services.database_service import database_service
        return database_service.list_documents(page, page_size)


# Global service instance
document_processing_service = DocumentProcessingService()
