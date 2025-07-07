"""Storage management service for file organization and management."""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file storage with organized directory structure."""

    def __init__(self):
        """Initialize storage service with configured paths."""
        self.base_path = Path(settings.storage_base_path)
        self.upload_path = self.base_path / settings.upload_dir
        self.processed_path = self.base_path / settings.processed_dir
        self.temp_path = self.base_path / settings.temp_dir
        
        # Create directory structure
        self._create_directory_structure()
        
        logger.info(f"Storage service initialized with base path: {self.base_path}")

    def _create_directory_structure(self):
        """Create the organized directory structure."""
        directories = [
            self.base_path,
            self.upload_path,
            self.processed_path,
            self.temp_path,
            # Upload subdirectories by file type
            self.upload_path / "pdf",
            self.upload_path / "docx", 
            self.upload_path / "pptx",
            self.upload_path / "txt",
            self.upload_path / "md",
            self.upload_path / "other",
            # Processed subdirectories
            self.processed_path / "markdown",
            self.processed_path / "chunks",
            self.processed_path / "images",
            self.processed_path / "metadata",
            # Temp subdirectories
            self.temp_path / "conversion",
            self.temp_path / "processing"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        logger.info("Storage directory structure created successfully")

    def get_upload_path(self, file_type: str) -> Path:
        """Get the upload path for a specific file type."""
        file_type_lower = file_type.lower()
        if file_type_lower in ["pdf", "docx", "pptx", "txt", "md"]:
            return self.upload_path / file_type_lower
        else:
            return self.upload_path / "other"

    def get_processed_path(self, content_type: str) -> Path:
        """Get the processed path for a specific content type."""
        valid_types = ["markdown", "chunks", "images", "metadata"]
        if content_type in valid_types:
            return self.processed_path / content_type
        else:
            raise ValueError(f"Invalid content type: {content_type}")

    def get_temp_path(self, operation: str) -> Path:
        """Get the temp path for a specific operation."""
        valid_operations = ["conversion", "processing"]
        if operation in valid_operations:
            return self.temp_path / operation
        else:
            return self.temp_path

    def store_uploaded_file(self, file_id: str, filename: str, file_type: str, 
                           temp_file_path: str) -> Dict[str, str]:
        """Store uploaded file in organized structure."""
        try:
            # Get target directory
            target_dir = self.get_upload_path(file_type)
            
            # Create filename with timestamp for uniqueness
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{file_id}_{timestamp}_{filename}"
            target_path = target_dir / safe_filename
            
            # Move file from temp location to organized storage
            shutil.move(temp_file_path, target_path)
            
            logger.info(f"File stored: {filename} -> {target_path}")
            
            return {
                "storage_path": str(target_path),
                "relative_path": str(target_path.relative_to(self.base_path)),
                "directory": str(target_dir),
                "safe_filename": safe_filename
            }
            
        except Exception as e:
            logger.error(f"Error storing file {file_id}: {str(e)}")
            raise

    def store_processed_content(self, file_id: str, content_type: str, 
                               content: str, filename: str = None) -> Dict[str, str]:
        """Store processed content (markdown, chunks, etc.)."""
        try:
            target_dir = self.get_processed_path(content_type)
            
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                extension = self._get_extension_for_content_type(content_type)
                filename = f"{file_id}_{timestamp}.{extension}"
            
            target_path = target_dir / filename
            
            # Write content to file
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Processed content stored: {content_type} -> {target_path}")
            
            return {
                "storage_path": str(target_path),
                "relative_path": str(target_path.relative_to(self.base_path)),
                "directory": str(target_dir),
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"Error storing processed content for {file_id}: {str(e)}")
            raise

    def store_processed_file(self, file_id: str, content_type: str, 
                            source_path: str, filename: str = None) -> Dict[str, str]:
        """Store processed file (images, etc.)."""
        try:
            target_dir = self.get_processed_path(content_type)
            
            source_file = Path(source_path)
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{file_id}_{timestamp}_{source_file.name}"
            
            target_path = target_dir / filename
            
            # Copy file to target location
            shutil.copy2(source_path, target_path)
            
            logger.info(f"Processed file stored: {content_type} -> {target_path}")
            
            return {
                "storage_path": str(target_path),
                "relative_path": str(target_path.relative_to(self.base_path)),
                "directory": str(target_dir),
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"Error storing processed file for {file_id}: {str(e)}")
            raise

    def _get_extension_for_content_type(self, content_type: str) -> str:
        """Get file extension for content type."""
        extensions = {
            "markdown": "md",
            "chunks": "json",
            "metadata": "json"
        }
        return extensions.get(content_type, "txt")

    def get_file_info(self, file_path: str) -> Dict:
        """Get information about a stored file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"exists": False}
            
            stat = path.stat()
            return {
                "exists": True,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "absolute_path": str(path.absolute()),
                "relative_path": str(path.relative_to(self.base_path)) if str(path).startswith(str(self.base_path)) else None
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return {"exists": False, "error": str(e)}

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage."""
        try:
            path = Path(file_path)
            if path.exists():
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                logger.info(f"Deleted: {file_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False

    def list_files(self, directory_type: str, file_type: str = None) -> List[Dict]:
        """List files in a specific directory."""
        try:
            if directory_type == "uploads":
                base_dir = self.upload_path
            elif directory_type == "processed":
                base_dir = self.processed_path
            elif directory_type == "temp":
                base_dir = self.temp_path
            else:
                raise ValueError(f"Invalid directory type: {directory_type}")
            
            if file_type:
                target_dir = base_dir / file_type
            else:
                target_dir = base_dir
            
            if not target_dir.exists():
                return []
            
            files = []
            for file_path in target_dir.rglob("*"):
                if file_path.is_file():
                    file_info = self.get_file_info(str(file_path))
                    file_info["name"] = file_path.name
                    file_info["path"] = str(file_path)
                    files.append(file_info)
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files in {directory_type}/{file_type}: {str(e)}")
            return []

    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """Clean up temporary files older than specified hours."""
        try:
            from datetime import datetime, timedelta
            
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            deleted_count = 0
            
            for file_path in self.temp_path.rglob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} temporary files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during temp file cleanup: {str(e)}")
            return 0

    def get_storage_stats(self) -> Dict:
        """Get storage usage statistics."""
        try:
            stats = {
                "base_path": str(self.base_path),
                "total_size": 0,
                "directories": {}
            }
            
            for dir_name, dir_path in [
                ("uploads", self.upload_path),
                ("processed", self.processed_path),
                ("temp", self.temp_path)
            ]:
                dir_stats = self._get_directory_stats(dir_path)
                stats["directories"][dir_name] = dir_stats
                stats["total_size"] += dir_stats["total_size"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {"error": str(e)}

    def _get_directory_stats(self, directory: Path) -> Dict:
        """Get statistics for a specific directory."""
        try:
            total_size = 0
            file_count = 0
            
            if directory.exists():
                for file_path in directory.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        file_count += 1
            
            return {
                "path": str(directory),
                "exists": directory.exists(),
                "total_size": total_size,
                "file_count": file_count,
                "size_mb": round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting directory stats for {directory}: {str(e)}")
            return {"error": str(e)}


# Global service instance
storage_service = StorageService()
