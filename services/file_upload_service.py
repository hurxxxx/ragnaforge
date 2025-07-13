"""File upload and management service."""

import os
import uuid
import time
import shutil
import hashlib
import logging
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
        logger.info(f"File upload service initialized with temp_dir: {self.temp_dir}")
    
    def _get_file_type(self, filename: str) -> Optional[SupportedFileType]:
        """Determine file type from filename extension."""
        extension = Path(filename).suffix.lower()
        
        type_mapping = {
            '.pdf': SupportedFileType.PDF,
            '.docx': SupportedFileType.DOCX,
            '.pptx': SupportedFileType.PPTX,
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
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()

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
            
            # Save file to temporary location first
            logger.info(f"💾 임시 파일 저장 시작: {temp_file_path}")
            file_size = 0
            file_hash = None
            with open(temp_file_path, "wb") as buffer:
                content = await file.read()
                file_size = len(content)
                logger.info(f"📊 파일 크기: {file_size / (1024*1024):.2f}MB")

                # Check file size after reading
                if file_size > self.max_file_size:
                    logger.error(f"❌ 파일 크기 초과: {file_size / (1024*1024):.1f}MB > {self.max_file_size / (1024*1024):.1f}MB")
                    # Clean up
                    if temp_file_path.exists():
                        temp_file_path.unlink()
                    return {
                        "success": False,
                        "error": f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum limit of {self.max_file_size / (1024*1024):.1f}MB",
                        "upload_time": time.time() - start_time
                    }

                # Calculate file hash for duplicate detection
                file_hash = self._calculate_file_hash(content)
                logger.info(f"🔍 파일 해시 계산 완료: {file_hash[:16]}...")

                buffer.write(content)
                logger.info(f"✅ 파일 저장 완료: {file_size} bytes")

            # Check for duplicate files using hash
            logger.info(f"🔍 중복 파일 검사 시작")
            from services.database_service import database_service
            existing_file = database_service.find_file_by_hash(file_hash)

            if existing_file:
                logger.info(f"📋 중복 파일 발견: {existing_file['filename']} (업로드 횟수: {existing_file['upload_count']})")

                # Increment upload count for existing file
                database_service.increment_upload_count(existing_file['file_id'])

                # Clean up temporary file
                if temp_file_path.exists():
                    temp_file_path.unlink()

                return {
                    "success": True,
                    "duplicate_detected": True,
                    "existing_file": {
                        "file_id": existing_file["file_id"],
                        "filename": existing_file["filename"],
                        "file_type": existing_file["file_type"],
                        "file_size": existing_file["file_size"],
                        "upload_count": existing_file["upload_count"] + 1,
                        "original_upload_time": existing_file["created_at"]
                    },
                    "message": f"동일한 파일이 이미 존재합니다: {existing_file['filename']}",
                    "upload_time": time.time() - start_time
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

            # Store in database
            from services.database_service import database_service
            database_service.store_file(file_metadata)
            
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
