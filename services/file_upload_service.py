"""File upload and management service."""

import os
import uuid
import time
import shutil
import hashlib
import logging
from functools import lru_cache
from typing import Dict, Optional, Tuple, List
from pathlib import Path
from typing import Dict, Optional, Tuple
from fastapi import UploadFile, HTTPException
from models import SupportedFileType
from config import settings

logger = logging.getLogger(__name__)


class FileUploadService:
    """Service for handling file uploads and management."""

    def __init__(self):
        # Use settings for configuration
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024  # Convert MB to bytes
        self.temp_dir = Path(settings.storage_base_path) / settings.temp_dir / "uploads"

        # Create temp directory if it doesn't exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Performance optimization: cache for recent hash lookups
        self._hash_cache = {}
        self._cache_max_size = 1000

        logger.info(f"File upload service initialized with temp_dir: {self.temp_dir}")
    
    def _get_file_type(self, filename: str) -> Optional[SupportedFileType]:
        """Determine file type from filename extension."""
        extension = Path(filename).suffix.lower()
        
        type_mapping = {
            '.pdf': SupportedFileType.PDF,
            '.docx': SupportedFileType.DOCX,
            '.pptx': SupportedFileType.PPTX,
            '.xlsx': SupportedFileType.XLSX,
            '.txt': SupportedFileType.TXT,
            '.md': SupportedFileType.MD,
        }
        
        return type_mapping.get(extension)
    
    def _validate_file(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """Validate uploaded file."""
        # Check file type
        file_type = self._get_file_type(file.filename)
        if not file_type:
            return False, f"Unsupported file type. Supported types: {', '.join([ft.value for ft in SupportedFileType])}"

        # Check file size (if we can get it)
        if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
            return False, f"File size exceeds maximum limit of {self.max_file_size / (1024*1024):.1f}MB"

        return True, None

    def _calculate_file_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content with fallback."""
        try:
            # For large files (>10MB), use chunked processing to reduce memory usage
            if len(content) > 10 * 1024 * 1024:  # 10MB
                return self._calculate_chunked_hash(content)
            else:
                return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.warning(f"SHA-256 hash calculation failed: {e}")
            # Fallback to MD5 if SHA-256 fails
            try:
                return f"md5_{hashlib.md5(content).hexdigest()}"
            except Exception as e2:
                logger.error(f"MD5 hash calculation also failed: {e2}")
                # Last resort: use file size + timestamp as identifier
                import time
                return f"fallback_{len(content)}_{int(time.time() * 1000000)}"

    def _calculate_chunked_hash(self, content: bytes, chunk_size: int = 8192) -> str:
        """Calculate hash using chunked processing for memory efficiency."""
        try:
            hash_obj = hashlib.sha256()

            # Process content in chunks
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                hash_obj.update(chunk)

            return hash_obj.hexdigest()
        except Exception as e:
            logger.error(f"Chunked hash calculation failed: {e}")
            raise

    async def _calculate_file_hash_async(self, content: bytes) -> str:
        """Calculate file hash asynchronously for better performance."""
        import asyncio
        import concurrent.futures

        # For very large files (>50MB), use thread pool for hash calculation
        if len(content) > 50 * 1024 * 1024:  # 50MB
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                return await loop.run_in_executor(executor, self._calculate_file_hash, content)
        else:
            return self._calculate_file_hash(content)

    def _check_hash_cache(self, file_hash: str) -> Optional[Dict]:
        """Check if file hash exists in cache."""
        return self._hash_cache.get(file_hash)

    def _update_hash_cache(self, file_hash: str, file_info: Dict):
        """Update hash cache with file information."""
        # Implement LRU-like behavior
        if len(self._hash_cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO for now)
            oldest_key = next(iter(self._hash_cache))
            del self._hash_cache[oldest_key]

        self._hash_cache[file_hash] = file_info

    def clear_cache(self):
        """Clear the hash cache."""
        self._hash_cache.clear()
        logger.info("Hash cache cleared")

    def _generate_fallback_identifier(self, filename: str, file_size: int, timestamp: float) -> str:
        """Generate fallback identifier when hash calculation fails."""
        # Use filename + size + timestamp for identification
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")[:50]
        return f"fallback_{safe_filename}_{file_size}_{int(timestamp * 1000000)}"

    async def upload_file(self, file: UploadFile) -> Dict:
        """Upload and store file."""
        start_time = time.time()



        logger.info(f"📁 파일 업로드 시작: {file.filename} ({getattr(file, 'size', 'unknown')} bytes)")

        try:
            # Validate file
            is_valid, error_msg = self._validate_file(file)
            if not is_valid:
                logger.error(f"❌ 파일 검증 실패: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "upload_time": time.time() - start_time
                }

            logger.info(f"✅ 파일 검증 통과: {file.content_type}")

            # Generate unique file ID
            file_id = str(uuid.uuid4())
            file_type = self._get_file_type(file.filename)
            logger.info(f"🆔 파일 ID 생성: {file_id}, 타입: {file_type}")

            # Create temporary filename for initial upload
            temp_filename = f"{file_id}_{file.filename}"
            temp_file_path = self.temp_dir / temp_filename
            
            # Save file to temporary location first with memory-efficient processing
            logger.info(f"💾 임시 파일 저장 시작: {temp_file_path}")
            file_size = 0
            file_hash = None

            # For large files, use streaming approach to reduce memory usage
            content = await file.read()
            file_size = len(content)
            logger.info(f"📊 파일 크기: {file_size / (1024*1024):.2f}MB")

            # Check for empty files
            if file_size == 0:
                logger.error(f"❌ 빈 파일 거부: {file.filename}")
                return {
                    "success": False,
                    "file_id": "",
                    "filename": file.filename,
                    "file_type": self._get_file_type(file.filename).value if self._get_file_type(file.filename) else "unknown",
                    "file_size": 0,
                    "upload_time": time.time() - start_time,
                    "temp_path": "",
                    "storage_path": None,
                    "relative_path": None,
                    "error": "Empty files are not allowed. Please upload a file with content.",
                    "duplicate_detected": False,
                    "existing_file": None,
                    "file_hash": None,
                    "upload_count": 0,
                    "message": None
                }

            # Check file size after reading
            if file_size > self.max_file_size:
                logger.error(f"❌ 파일 크기 초과: {file_size / (1024*1024):.1f}MB > {self.max_file_size / (1024*1024):.1f}MB")
                return {
                    "success": False,
                    "error": f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum limit of {self.max_file_size / (1024*1024):.1f}MB",
                    "upload_time": time.time() - start_time
                }

            # Calculate file hash for duplicate detection (async for large files)
            hash_start_time = time.time()
            try:
                file_hash = await self._calculate_file_hash_async(content)
                hash_duration = (time.time() - hash_start_time) * 1000  # Convert to ms



                logger.info(f"🔍 파일 해시 계산 완료: {file_hash[:16]}... ({hash_duration:.1f}ms)")
            except Exception as e:
                hash_duration = (time.time() - hash_start_time) * 1000



                logger.error(f"파일 해시 계산 실패: {e}")
                # Use fallback identifier
                file_hash = self._generate_fallback_identifier(file.filename, file_size, time.time())
                logger.warning(f"대체 식별자 사용: {file_hash[:16]}...")

            # Write file to disk
            with open(temp_file_path, "wb") as buffer:
                buffer.write(content)
            logger.info(f"✅ 파일 저장 완료: {file_size} bytes")

            # Clear content from memory for large files
            if file_size > 10 * 1024 * 1024:  # 10MB
                del content
                import gc
                gc.collect()
                logger.info(f"🧹 대용량 파일 메모리 정리 완료")

            # Check for duplicate files using hash (with cache) - only if enabled
            existing_file = None
            detection_method = "disabled"

            if settings.enable_hash_duplicate_check:
                logger.info(f"🔍 중복 파일 검사 시작")
                duplicate_check_start = time.time()

                # First check cache
                existing_file = self._check_hash_cache(file_hash)
                detection_method = "cache"

                if existing_file:
                    logger.info(f"📋 캐시에서 중복 파일 발견: {existing_file['filename']}")
                else:
                    # Check database if not in cache
                    from services.database_service import database_service
                    existing_file = database_service.find_file_by_hash(file_hash)
                    detection_method = "database"

                    # Update cache if found
                    if existing_file:
                        self._update_hash_cache(file_hash, existing_file)
            else:
                logger.info(f"🔍 중복 파일 검사 비활성화됨 (ENABLE_HASH_DUPLICATE_CHECK=false)")
                duplicate_check_start = time.time()

            duplicate_check_duration = (time.time() - duplicate_check_start) * 1000



            if existing_file:
                new_upload_count = existing_file['upload_count'] + 1
                logger.info(f"📋 중복 파일 발견: {existing_file['filename']} (업로드 횟수: {new_upload_count})")



                # Increment upload count for existing file
                from services.database_service import database_service
                database_service.increment_upload_count(existing_file['file_id'])

                # Clean up temporary file
                if temp_file_path.exists():
                    temp_file_path.unlink()



                return {
                    "success": True,
                    "file_id": existing_file["file_id"],
                    "filename": file.filename,
                    "file_type": file_type.value,
                    "file_size": file_size,
                    "upload_time": time.time() - start_time,
                    "temp_path": str(temp_file_path),
                    "storage_path": existing_file.get("storage_path", ""),
                    "relative_path": existing_file.get("relative_path", ""),
                    "error": None,
                    "duplicate_detected": True,
                    "existing_file": {
                        "file_id": existing_file["file_id"],
                        "filename": existing_file["filename"],
                        "file_type": existing_file["file_type"],
                        "file_size": existing_file["file_size"],
                        "upload_count": new_upload_count,
                        "original_upload_time": existing_file["created_at"]
                    },
                    "file_hash": file_hash,
                    "upload_count": new_upload_count,
                    "message": f"동일한 파일이 이미 존재합니다: {existing_file['filename']}"
                }
            
            # Move file to organized storage using storage service
            logger.info(f"📂 스토리지 서비스로 파일 이동 시작")
            from services.storage_service import storage_service
            storage_info = storage_service.store_uploaded_file(
                file_id=file_id,
                filename=file.filename,
                file_type=file_type.value,
                temp_file_path=str(temp_file_path)
            )
            logger.info(f"✅ 스토리지 저장 완료: {storage_info.get('file_path', 'N/A')}")

            upload_time = time.time() - start_time

            # Store file metadata
            file_metadata = {
                "file_id": file_id,
                "filename": file.filename,
                "safe_filename": storage_info["safe_filename"],
                "file_type": file_type,
                "file_size": file_size,
                "temp_path": storage_info["storage_path"],  # Now points to organized storage
                "storage_path": storage_info["storage_path"],
                "relative_path": storage_info["relative_path"],
                "upload_time": upload_time,
                "created_at": time.time(),
                "file_hash": file_hash,
                "upload_count": 1
            }

            # Store in database with error handling
            from services.database_service import database_service
            try:
                success = database_service.store_file(file_metadata)
                if not success:
                    # Database storage failed, clean up uploaded file
                    logger.error(f"데이터베이스 저장 실패, 업로드된 파일 정리: {storage_info['storage_path']}")
                    try:
                        Path(storage_info["storage_path"]).unlink(missing_ok=True)
                    except Exception as cleanup_error:
                        logger.error(f"파일 정리 실패: {cleanup_error}")

                    return {
                        "success": False,
                        "error": "Database storage failed",
                        "upload_time": time.time() - start_time
                    }
            except Exception as db_error:
                logger.error(f"데이터베이스 저장 중 예외 발생: {db_error}")
                # Clean up uploaded file
                try:
                    Path(storage_info["storage_path"]).unlink(missing_ok=True)
                except Exception as cleanup_error:
                    logger.error(f"파일 정리 실패: {cleanup_error}")

                return {
                    "success": False,
                    "error": f"Database error: {str(db_error)}",
                    "upload_time": time.time() - start_time
                }
            
            logger.info(f"File uploaded successfully: {file.filename} -> {file_id}")



            return {
                "success": True,
                "duplicate_detected": False,
                "file_id": file_id,
                "filename": file.filename,
                "file_type": file_type,
                "file_size": file_size,
                "upload_time": upload_time,
                "temp_path": storage_info["storage_path"],  # Return organized storage path
                "storage_path": storage_info["storage_path"],
                "relative_path": storage_info["relative_path"],
                "file_hash": file_hash,
                "upload_count": 1
            }
            
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {str(e)}")



            return {
                "success": False,
                "error": f"Upload failed: {str(e)}",
                "upload_time": time.time() - start_time
            }
    
    def get_file_info(self, file_id: str) -> Optional[Dict]:
        """Get file information by ID."""
        from services.database_service import database_service
        return database_service.get_file(file_id)
    
    def get_file_path(self, file_id: str) -> Optional[Path]:
        """Get file path by ID."""
        file_info = self.get_file_info(file_id)
        if file_info:
            # Try storage_path first, fallback to temp_path for backward compatibility
            path = file_info.get("storage_path") or file_info.get("temp_path")
            return Path(path) if path else None
        return None
    
    def delete_file(self, file_id: str) -> bool:
        """Delete uploaded file."""
        try:
            file_info = self.get_file_info(file_id)
            if not file_info:
                return False

            # Delete physical file using storage service
            from services.storage_service import storage_service
            file_path = file_info.get("storage_path") or file_info.get("temp_path")
            if file_path:
                storage_service.delete_file(file_path)

            # Remove from database
            from services.database_service import database_service
            success = database_service.delete_file(file_id)

            if success:
                logger.info(f"File deleted: {file_id}")
            return success

        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            return False
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up files older than specified hours."""
        try:
            from services.database_service import database_service
            old_files = database_service.get_old_files(max_age_hours)

            files_deleted = 0
            for file_info in old_files:
                if self.delete_file(file_info["id"]):
                    files_deleted += 1

            if files_deleted > 0:
                logger.info(f"Cleaned up {files_deleted} old files")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


# Global service instance
file_upload_service = FileUploadService()
