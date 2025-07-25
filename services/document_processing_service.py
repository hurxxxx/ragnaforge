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
from services.unified_search_service import unified_search_service
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

        # Auto selection logic - choose best engine for each format
        if file_type == SupportedFileType.PDF:
            return "marker"  # Marker excels at PDF conversion
        elif file_type in [SupportedFileType.DOCX, SupportedFileType.PPTX, SupportedFileType.XLSX]:
            return "docling"  # Docling has native Office document support
        else:
            return "docling"  # Fallback to docling for other formats
    
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
        logger.info(f"📄 문서 변환 시작: {file_path.name} (타입: {file_type.value}, 방법: {method})")
        start_time = time.time()

        try:
            if file_type in [SupportedFileType.TXT, SupportedFileType.MD]:
                # For text files, just read the content
                logger.info(f"📖 텍스트 파일 직접 읽기")
                content = self._read_text_file(file_path)
                logger.info(f"✅ 텍스트 읽기 완료: {len(content)} 문자")
                return {
                    "success": True,
                    "markdown_content": content,
                    "markdown_length": len(content),
                    "conversion_time": 0.1,
                    "method_used": "direct_read"
                }
            
            elif file_type == SupportedFileType.PDF:
                logger.info(f"📄 PDF 변환 시작 - 방법: {method}")
                if method == "marker":
                    logger.info(f"🔄 Marker 서비스로 PDF 변환 중...")
                    result = marker_service.convert_pdf_to_markdown(
                        pdf_path=str(file_path),
                        output_dir="temp_processing",
                        extract_images=extract_images
                    )
                else:  # docling
                    logger.info(f"🔄 Docling 서비스로 PDF 변환 중...")
                    result = docling_service.convert_pdf_to_markdown(
                        pdf_path=str(file_path),
                        output_dir="temp_processing",
                        extract_images=extract_images
                    )
                
                if result.get("success"):
                    conversion_time = time.time() - start_time
                    markdown_length = result.get("markdown_length", 0)
                    logger.info(f"✅ PDF 변환 성공: {markdown_length} 문자, {conversion_time:.2f}초")
                    return {
                        "success": True,
                        "markdown_content": result.get("markdown", ""),
                        "markdown_length": markdown_length,
                        "conversion_time": conversion_time,
                        "method_used": method
                    }
                else:
                    logger.error(f"❌ PDF 변환 실패: {result.get('error', 'Conversion failed')}")
                    return {
                        "success": False,
                        "error": result.get("error", "Conversion failed"),
                        "method_used": method
                    }
            
            elif file_type in [SupportedFileType.DOCX, SupportedFileType.PPTX, SupportedFileType.XLSX]:
                # Office documents - use Docling (recommended) or fallback to Marker
                logger.info(f"📄 Office 문서 변환 시작 - 방법: {method}")
                if method == "docling" or method == "auto":
                    logger.info(f"🔄 Docling 서비스로 Office 문서 변환 중...")
                    result = docling_service.convert_office_to_markdown(
                        file_path=str(file_path),
                        output_dir="temp_processing"
                    )
                else:  # marker (fallback, but not ideal for Office docs)
                    logger.warning(f"⚠️ Marker는 Office 문서에 최적화되지 않음. Docling 사용을 권장합니다.")
                    logger.info(f"🔄 Marker 서비스로 Office 문서 변환 시도 중...")
                    # Marker doesn't directly support Office docs, so this might fail
                    try:
                        result = marker_service.convert_pdf_to_markdown(
                            pdf_path=str(file_path),
                            output_dir="temp_processing",
                            extract_images=extract_images
                        )
                    except Exception as e:
                        logger.error(f"Marker로 Office 문서 변환 실패: {e}")
                        logger.info("Docling으로 대체 시도...")
                        result = docling_service.convert_office_to_markdown(
                            file_path=str(file_path),
                            output_dir="temp_processing"
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
            logger.info(f"🔢 임베딩 생성 시작: {len(chunks)}개 청크, 모델={model}")
            texts = [chunk["text"] for chunk in chunks]
            logger.info(f"📝 텍스트 추출 완료: 평균 길이={sum(len(t) for t in texts) / len(texts):.1f}자")

            embeddings = embedding_service.encode_texts(texts, model)
            logger.info(f"🧠 임베딩 인코딩 완료: shape={embeddings.shape}")

            # Add embeddings to chunks
            for i, chunk in enumerate(chunks):
                chunk["embedding"] = embeddings[i].tolist()

            logger.info(f"✅ 임베딩 생성 성공: {len(chunks)}개 청크 처리 완료")
            return True

        except Exception as e:
            logger.error(f"❌ 임베딩 생성 실패: {str(e)}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return False
    
    async def process_document(self, file_id: str, conversion_method: str = "auto",
                              extract_images: bool = False, chunk_strategy: Optional[str] = None,
                              chunk_size: Optional[int] = None, overlap: Optional[int] = None,
                              generate_embeddings: bool = True, embedding_model: Optional[str] = None,
                              enable_hash_check: Optional[bool] = None) -> Dict:
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

            # Check if this is a duplicate file and if it's already been processed
            from services.database_service import database_service
            file_hash = file_info.get("file_hash")

            # Determine if hash check should be enabled for this request
            # Priority: request parameter > system default setting
            hash_check_enabled = enable_hash_check if enable_hash_check is not None else settings.enable_hash_duplicate_check

            # Check for duplicate documents using hash - only if enabled
            existing_document = None
            if file_hash and hash_check_enabled:
                logger.info(f"🔍 중복 문서 검사 시작 (요청별 설정: {enable_hash_check}, 시스템 기본값: {settings.enable_hash_duplicate_check}): {file_hash[:16]}...")
                existing_document = database_service.find_document_by_file_hash(file_hash)

                if existing_document:
                    logger.info(f"📋 기존 처리된 문서 발견: {existing_document['filename']} (문서 ID: {existing_document['id']})")

                    # Return existing document information
                    return {
                        "success": True,
                        "duplicate_detected": True,
                        "existing_document": True,
                        "file_id": file_id,
                        "document_id": existing_document["id"],
                        "filename": file_info["filename"],
                        "original_filename": existing_document["filename"],
                        "conversion_method": existing_document["conversion_method"],
                        "conversion_time": existing_document["conversion_time"],
                        "markdown_content": existing_document["markdown_content"],
                        "markdown_length": existing_document.get("markdown_length", 0),
                        "total_chunks": existing_document.get("total_chunks", 0),
                        "chunks": existing_document.get("chunks", []),
                        "embeddings_generated": existing_document.get("embeddings_generated", False),
                        "processing_time": time.time() - start_time,
                        "original_processing_time": existing_document.get("processing_time", 0),
                        "original_created_at": existing_document.get("created_at", 0),
                        "message": f"동일한 파일이 이미 처리되었습니다: {existing_document['filename']}"
                    }
                else:
                    logger.info(f"✅ 새로운 파일 - 문서 처리 진행")
            elif file_hash and not hash_check_enabled:
                logger.info(f"🔍 중복 문서 검사 비활성화됨 (요청 설정: {enable_hash_check}, 시스템 기본값: {settings.enable_hash_duplicate_check})")
            else:
                logger.warning(f"⚠️ 파일 해시 정보 없음 - 중복 검사 스킵")
            
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
            file_type_str = file_info["file_type"]
            # Convert string to SupportedFileType enum
            try:
                file_type = SupportedFileType(file_type_str.lower())
            except ValueError:
                # Fallback for common extensions
                if file_type_str.lower() == "pdf":
                    file_type = SupportedFileType.PDF
                elif file_type_str.lower() in ["txt", "text"]:
                    file_type = SupportedFileType.TXT
                elif file_type_str.lower() in ["md", "markdown"]:
                    file_type = SupportedFileType.MD
                else:
                    file_type = SupportedFileType.PDF  # Default fallback

            logger.info(f"📋 파일 타입 확인: {file_type_str} -> {file_type}")
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
            logger.info(f"✂️ 텍스트 청킹 시작: 전략={chunk_strategy}, 크기={chunk_size}, 오버랩={overlap}")
            chunks = self._chunk_text(markdown_content, chunk_strategy, chunk_size, overlap)
            logger.info(f"✅ 청킹 완료: {len(chunks)}개 청크 생성")

            # Generate embeddings if requested
            embeddings_generated = False
            if generate_embeddings and chunks:
                logger.info(f"🔢 임베딩 생성 시작: 모델={embedding_model}")
                embeddings_generated = self._generate_embeddings(chunks, embedding_model)
                if embeddings_generated:
                    logger.info(f"✅ 임베딩 생성 완료")
                else:
                    logger.warning(f"⚠️ 임베딩 생성 실패")
            
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

            # Store in database with error handling
            from services.database_service import database_service
            try:
                success = database_service.store_document(processed_doc)
                if not success:
                    logger.error(f"문서 데이터베이스 저장 실패: {document_id}")
                    # Clean up stored files
                    try:
                        Path(markdown_storage["storage_path"]).unlink(missing_ok=True)
                        Path(chunks_storage["storage_path"]).unlink(missing_ok=True)
                    except Exception as cleanup_error:
                        logger.error(f"처리된 파일 정리 실패: {cleanup_error}")

                    return {
                        "success": False,
                        "error": "Failed to store document in database",
                        "processing_time": time.time() - start_time
                    }
            except Exception as db_error:
                logger.error(f"문서 저장 중 예외 발생: {db_error}")
                # Clean up stored files
                try:
                    Path(markdown_storage["storage_path"]).unlink(missing_ok=True)
                    Path(chunks_storage["storage_path"]).unlink(missing_ok=True)
                except Exception as cleanup_error:
                    logger.error(f"처리된 파일 정리 실패: {cleanup_error}")

                return {
                    "success": False,
                    "error": f"Database error during document storage: {str(db_error)}",
                    "processing_time": time.time() - start_time
                }

            # Store in unified search service if embeddings were generated
            if embeddings_generated and chunks:
                try:

                    # Check if document with same hash already exists in vector DB - only if enabled
                    existing_in_vector_db = None
                    if file_hash and hash_check_enabled:
                        logger.info(f"🔍 벡터 DB 중복 검사 시작")
                        existing_in_vector_db = await unified_search_service.check_document_exists_by_hash(file_hash)
                    elif file_hash and not hash_check_enabled:
                        logger.info(f"🔍 벡터 DB 중복 검사 비활성화됨 (요청 설정: {enable_hash_check}, 시스템 기본값: {settings.enable_hash_duplicate_check})")

                        if existing_in_vector_db:
                            logger.info(f"📋 벡터 DB에 동일 문서 존재 - 저장 스킵: {existing_in_vector_db}")
                        else:
                            logger.info(f"✅ 벡터 DB에 새 문서 저장 진행")

                            # Prepare documents for unified search service
                            # 1. Qdrant용 청크 문서들 (벡터 검색용)
                            chunk_documents = []
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
                                    "file_type": file_type.value,
                                    "chunk_index": i,
                                    "file_size": file_info.get("size", 0),
                                    "created_at": time.time(),
                                    "metadata": {
                                        "filename": file_info["filename"],
                                        "file_type": file_type.value,
                                        "conversion_method": method,
                                        "created_at": time.time(),
                                        "embedding_model": embedding_model,
                                        "document_id": document_id,
                                        "chunk_index": i,
                                        "text": chunk_text,  # Qdrant용 text 필드
                                        "content": chunk_text,  # MeiliSearch용 content 필드
                                        "file_hash": file_hash  # 중복 검사용 해시 추가
                                    }
                                }
                                chunk_documents.append(doc)

                            # 2. Meilisearch용 전체 문서 (풀텍스트 검색용)
                            full_document = {
                                "id": document_id,  # 전체 문서는 document_id를 그대로 사용
                                "document_id": document_id,
                                "content": markdown_content,  # 전체 마크다운 내용
                                "title": file_info["filename"],
                                "file_name": file_info["filename"],
                                "file_type": file_type.value,
                                "file_size": file_info.get("size", 0),
                                "created_at": time.time(),
                                "chunk_count": len(chunks),  # 청크 개수 정보
                                "metadata": {
                                    "filename": file_info["filename"],
                                    "file_type": file_type.value,
                                    "conversion_method": method,
                                    "created_at": time.time(),
                                    "document_id": document_id,
                                    "content": markdown_content,  # MeiliSearch용 전체 내용
                                    "file_hash": file_hash,  # 중복 검사용 해시 추가
                                    "chunk_count": len(chunks)
                                }
                            }

                            # Store in unified search service (hybrid approach)
                            logger.info(f"💾 통합 검색 서비스에 문서 저장 시작: {len(chunk_documents)}개 청크 + 1개 전체 문서")
                            unified_success = await unified_search_service.store_documents(
                                documents=chunk_documents,
                                full_document=full_document
                            )

                            if unified_success:
                                logger.info(f"✅ 통합 검색 서비스 저장 완료: {document_id}")
                            else:
                                logger.error(f"❌ 통합 검색 서비스 저장 실패: {document_id}")
                    else:
                        logger.warning(f"⚠️ 파일 해시 없음 - 벡터 DB 중복 검사 스킵")

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
