"""File upload and management service."""

import os
import uuid
import time
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from fastapi import UploadFile, HTTPException
from models import SupportedFileType

logger = logging.getLogger(__name__)


class FileUploadService:
    """Service for handling file uploads and management."""

    def __init__(self, upload_dir: str = "uploads", max_file_size: int = 50 * 1024 * 1024):  # 50MB
        self.upload_dir = Path(upload_dir)
        self.max_file_size = max_file_size

        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(exist_ok=True)
        logger.info(f"File upload service initialized with upload_dir: {self.upload_dir}")
    
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
    
    async def upload_file(self, file: UploadFile) -> Dict:
        """Upload and store file."""
        start_time = time.time()
        
        try:
            # Validate file
            is_valid, error_msg = self._validate_file(file)
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg,
                    "upload_time": time.time() - start_time
                }
            
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            file_type = self._get_file_type(file.filename)
            
            # Create safe filename
            safe_filename = f"{file_id}_{file.filename}"
            file_path = self.upload_dir / safe_filename
            
            # Save file
            file_size = 0
            with open(file_path, "wb") as buffer:
                content = await file.read()
                file_size = len(content)
                
                # Check file size after reading
                if file_size > self.max_file_size:
                    # Clean up
                    if file_path.exists():
                        file_path.unlink()
                    return {
                        "success": False,
                        "error": f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum limit of {self.max_file_size / (1024*1024):.1f}MB",
                        "upload_time": time.time() - start_time
                    }
                
                buffer.write(content)
            
            upload_time = time.time() - start_time
            
            # Store file metadata
            file_metadata = {
                "file_id": file_id,
                "filename": file.filename,
                "safe_filename": safe_filename,
                "file_type": file_type,
                "file_size": file_size,
                "temp_path": str(file_path),
                "upload_time": upload_time,
                "created_at": time.time()
            }

            # Store in database
            from services.database_service import database_service
            database_service.store_file(file_metadata)
            
            logger.info(f"File uploaded successfully: {file.filename} -> {file_id}")
            
            return {
                "success": True,
                "file_id": file_id,
                "filename": file.filename,
                "file_type": file_type,
                "file_size": file_size,
                "upload_time": upload_time,
                "temp_path": str(file_path)
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
            return Path(file_info["temp_path"])
        return None
    
    def delete_file(self, file_id: str) -> bool:
        """Delete uploaded file."""
        try:
            file_info = self.get_file_info(file_id)
            if not file_info:
                return False

            # Delete physical file
            file_path = Path(file_info["temp_path"])
            if file_path.exists():
                file_path.unlink()

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
