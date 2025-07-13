"""SQLite database service for file and document metadata management."""

import sqlite3
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseService:
    """SQLite database service for metadata management."""
    
    def __init__(self, db_path: str = "data/ragnaforge.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._initialize_database()
        logger.info(f"Database service initialized: {self.db_path}")
    
    def _get_optimized_connection(self) -> sqlite3.Connection:
        """Get optimized SQLite connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        
        # Performance optimizations
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")  # Faster writes
        conn.execute("PRAGMA cache_size=10000")  # Increase cache
        conn.execute("PRAGMA temp_store=MEMORY")  # Temp data in memory
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory map
        
        return conn
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = self._get_optimized_connection()
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Initialize database tables and indexes."""
        with self.get_connection() as conn:
            # Files table for uploaded files
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    safe_filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    temp_path TEXT NOT NULL,
                    storage_path TEXT,
                    relative_path TEXT,
                    upload_time REAL NOT NULL,
                    created_at REAL NOT NULL,
                    status TEXT DEFAULT 'uploaded'
                )
            """)

            # Add new columns if they don't exist (for backward compatibility)
            try:
                conn.execute("ALTER TABLE files ADD COLUMN storage_path TEXT")
            except:
                pass  # Column already exists
            try:
                conn.execute("ALTER TABLE files ADD COLUMN relative_path TEXT")
            except:
                pass  # Column already exists
            try:
                conn.execute("ALTER TABLE files ADD COLUMN file_hash TEXT")
            except:
                pass  # Column already exists
            try:
                conn.execute("ALTER TABLE files ADD COLUMN upload_count INTEGER DEFAULT 1")
            except:
                pass  # Column already exists
            
            # Documents table for processed documents
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    conversion_method TEXT NOT NULL,
                    conversion_time REAL NOT NULL,
                    markdown_content TEXT,
                    markdown_storage_path TEXT,
                    chunks_storage_path TEXT,
                    markdown_length INTEGER NOT NULL,
                    total_chunks INTEGER NOT NULL,
                    embeddings_generated BOOLEAN NOT NULL,
                    processing_time REAL NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            """)

            # Add new columns if they don't exist (for backward compatibility)
            try:
                conn.execute("ALTER TABLE documents ADD COLUMN markdown_storage_path TEXT")
            except:
                pass  # Column already exists
            try:
                conn.execute("ALTER TABLE documents ADD COLUMN chunks_storage_path TEXT")
            except:
                pass  # Column already exists
            
            # Document chunks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    text_preview TEXT NOT NULL,
                    start_char INTEGER NOT NULL,
                    end_char INTEGER NOT NULL,
                    token_count INTEGER NOT NULL,
                    has_embedding BOOLEAN DEFAULT FALSE,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents (id)
                )
            """)
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_files_created_at ON files(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_files_file_type ON files(file_type)",
                "CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)",
                "CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash)",
                "CREATE INDEX IF NOT EXISTS idx_documents_file_id ON documents(file_id)",
                "CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type)",
                "CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id)",
                "CREATE INDEX IF NOT EXISTS idx_chunks_has_embedding ON document_chunks(has_embedding)"
            ]
            
            for index_sql in indexes:
                conn.execute(index_sql)
            
            conn.commit()
            logger.info("Database tables and indexes created successfully")
    
    # File operations
    def store_file(self, file_data: Dict) -> bool:
        """Store uploaded file metadata."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO files
                    (id, filename, safe_filename, file_type, file_size, temp_path, storage_path, relative_path, upload_time, created_at, file_hash, upload_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_data["file_id"],
                    file_data["filename"],
                    file_data["safe_filename"],
                    file_data["file_type"],
                    file_data["file_size"],
                    file_data["temp_path"],
                    file_data.get("storage_path"),
                    file_data.get("relative_path"),
                    file_data["upload_time"],
                    file_data["created_at"],
                    file_data.get("file_hash"),
                    file_data.get("upload_count", 1)
                ))
                conn.commit()
                logger.info(f"File stored in database: {file_data['file_id']}")
                return True
        except Exception as e:
            logger.error(f"Error storing file {file_data.get('file_id')}: {str(e)}")
            return False

    def find_file_by_hash(self, file_hash: str) -> Optional[Dict]:
        """Find existing file by hash."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, filename, file_type, file_size, storage_path, relative_path,
                           upload_time, created_at, upload_count
                    FROM files
                    WHERE file_hash = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (file_hash,))

                row = cursor.fetchone()
                if row:
                    return {
                        "file_id": row[0],
                        "filename": row[1],
                        "file_type": row[2],
                        "file_size": row[3],
                        "storage_path": row[4],
                        "relative_path": row[5],
                        "upload_time": row[6],
                        "created_at": row[7],
                        "upload_count": row[8]
                    }
                return None
        except Exception as e:
            logger.error(f"Error finding file by hash: {str(e)}")
            return None

    def increment_upload_count(self, file_id: str) -> bool:
        """Increment upload count for existing file."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE files
                    SET upload_count = upload_count + 1,
                        upload_time = ?
                    WHERE id = ?
                """, (time.time(), file_id))
                conn.commit()
                logger.info(f"Incremented upload count for file: {file_id}")
                return True
        except Exception as e:
            logger.error(f"Error incrementing upload count: {str(e)}")
            return False

    def find_document_by_file_hash(self, file_hash: str) -> Optional[Dict]:
        """Find existing processed document by file hash."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT d.* FROM documents d
                    JOIN files f ON d.file_id = f.id
                    WHERE f.file_hash = ?
                    ORDER BY d.created_at DESC
                    LIMIT 1
                """, (file_hash,))

                row = cursor.fetchone()
                if row:
                    document = dict(row)

                    # Get chunks for this document
                    chunk_rows = conn.execute("""
                        SELECT * FROM document_chunks
                        WHERE document_id = ?
                        ORDER BY chunk_index
                    """, (document["id"],)).fetchall()

                    document["chunks"] = [dict(chunk_row) for chunk_row in chunk_rows]
                    return document
                return None
        except Exception as e:
            logger.error(f"Error finding document by file hash: {str(e)}")
            return None

    def list_files(self, page: int = 1, page_size: int = 100) -> Dict:
        """List files with pagination and duplicate information."""
        try:
            offset = (page - 1) * page_size

            with self.get_connection() as conn:
                # Get total count
                total = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]

                # Get files with processing status
                rows = conn.execute("""
                    SELECT f.id, f.filename, f.file_type, f.file_size, f.upload_time,
                           f.created_at, f.file_hash, f.upload_count,
                           d.id as document_id
                    FROM files f
                    LEFT JOIN documents d ON f.id = d.file_id
                    ORDER BY f.created_at DESC
                    LIMIT ? OFFSET ?
                """, (page_size, offset)).fetchall()

                files = []
                for row in rows:
                    file_info = {
                        "file_id": row[0],
                        "filename": row[1],
                        "file_type": row[2],
                        "file_size": row[3],
                        "upload_time": row[4],
                        "created_at": row[5],
                        "file_hash": row[6],
                        "upload_count": row[7] or 1,
                        "is_duplicate": (row[7] or 1) > 1,
                        "is_processed": row[8] is not None,
                        "document_id": row[8]
                    }
                    files.append(file_info)

                return {
                    "files": files,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return {"files": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}

    def get_duplicate_stats(self) -> Dict:
        """Get statistics about duplicate files."""
        try:
            with self.get_connection() as conn:
                # Total files
                total_files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]

                # Unique files (by hash)
                unique_files = conn.execute("""
                    SELECT COUNT(DISTINCT file_hash) FROM files
                    WHERE file_hash IS NOT NULL
                """).fetchone()[0]

                # Duplicate groups (files with upload_count > 1)
                duplicate_groups = conn.execute("""
                    SELECT COUNT(*) FROM files
                    WHERE upload_count > 1
                """).fetchone()[0]

                # Total duplicates (sum of upload_count - 1 for each file)
                total_duplicates_result = conn.execute("""
                    SELECT SUM(upload_count - 1) FROM files
                    WHERE upload_count > 1
                """).fetchone()[0]
                total_duplicates = total_duplicates_result or 0

                # Storage saved (estimate: duplicate count * average file size)
                avg_size_result = conn.execute("""
                    SELECT AVG(file_size) FROM files
                    WHERE upload_count > 1
                """).fetchone()[0]
                avg_size = avg_size_result or 0
                storage_saved = int(total_duplicates * avg_size)

                return {
                    "total_files": total_files,
                    "unique_files": unique_files,
                    "duplicate_groups": duplicate_groups,
                    "total_duplicates": total_duplicates,
                    "storage_saved_bytes": storage_saved
                }
        except Exception as e:
            logger.error(f"Error getting duplicate stats: {str(e)}")
            return {
                "total_files": 0,
                "unique_files": 0,
                "duplicate_groups": 0,
                "total_duplicates": 0,
                "storage_saved_bytes": 0
            }

    def list_duplicate_groups(self, page: int = 1, page_size: int = 50) -> Dict:
        """List groups of duplicate files."""
        try:
            offset = (page - 1) * page_size

            with self.get_connection() as conn:
                # Get duplicate file hashes (upload_count > 1)
                hash_rows = conn.execute("""
                    SELECT file_hash, upload_count, MIN(created_at) as first_uploaded,
                           MAX(upload_time) as last_uploaded
                    FROM files
                    WHERE upload_count > 1 AND file_hash IS NOT NULL
                    GROUP BY file_hash
                    ORDER BY upload_count DESC, first_uploaded DESC
                    LIMIT ? OFFSET ?
                """, (page_size, offset)).fetchall()

                # Get total count
                total_groups = conn.execute("""
                    SELECT COUNT(DISTINCT file_hash) FROM files
                    WHERE upload_count > 1 AND file_hash IS NOT NULL
                """).fetchone()[0]

                duplicate_groups = []
                for hash_row in hash_rows:
                    file_hash = hash_row[0]

                    # Get all files with this hash
                    file_rows = conn.execute("""
                        SELECT f.id, f.filename, f.file_type, f.file_size, f.upload_time,
                               f.created_at, f.file_hash, f.upload_count,
                               d.id as document_id
                        FROM files f
                        LEFT JOIN documents d ON f.id = d.file_id
                        WHERE f.file_hash = ?
                        ORDER BY f.created_at ASC
                    """, (file_hash,)).fetchall()

                    files = []
                    is_processed = False
                    document_id = None

                    for file_row in file_rows:
                        file_info = {
                            "file_id": file_row[0],
                            "filename": file_row[1],
                            "file_type": file_row[2],
                            "file_size": file_row[3],
                            "upload_time": file_row[4],
                            "created_at": file_row[5],
                            "file_hash": file_row[6],
                            "upload_count": file_row[7],
                            "is_duplicate": True,
                            "is_processed": file_row[8] is not None,
                            "document_id": file_row[8]
                        }
                        files.append(file_info)

                        if file_row[8] is not None:
                            is_processed = True
                            document_id = file_row[8]

                    group = {
                        "file_hash": file_hash,
                        "files": files,
                        "total_uploads": hash_row[1],
                        "first_uploaded": hash_row[2],
                        "last_uploaded": hash_row[3],
                        "is_processed": is_processed,
                        "document_id": document_id
                    }
                    duplicate_groups.append(group)

                return {
                    "duplicate_groups": duplicate_groups,
                    "total_groups": total_groups,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total_groups + page_size - 1) // page_size
                }
        except Exception as e:
            logger.error(f"Error listing duplicate groups: {str(e)}")
            return {
                "duplicate_groups": [],
                "total_groups": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
    
    def get_file(self, file_id: str) -> Optional[Dict]:
        """Get file metadata by ID."""
        try:
            with self.get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM files WHERE id = ?", (file_id,)
                ).fetchone()
                
                if row:
                    return dict(row)
                return None
        except Exception as e:
            logger.error(f"Error getting file {file_id}: {str(e)}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """Delete file metadata."""
        try:
            with self.get_connection() as conn:
                # Delete related chunks first
                conn.execute("""
                    DELETE FROM document_chunks 
                    WHERE document_id IN (
                        SELECT id FROM documents WHERE file_id = ?
                    )
                """, (file_id,))
                
                # Delete documents
                conn.execute("DELETE FROM documents WHERE file_id = ?", (file_id,))
                
                # Delete file
                result = conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
                conn.commit()
                
                if result.rowcount > 0:
                    logger.info(f"File deleted from database: {file_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            return False
    
    def get_old_files(self, max_age_hours: int = 24) -> List[Dict]:
        """Get files older than specified hours."""
        try:
            max_age_seconds = max_age_hours * 3600
            cutoff_time = time.time() - max_age_seconds
            
            with self.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM files WHERE created_at < ?", (cutoff_time,)
                ).fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting old files: {str(e)}")
            return []
    
    # Document operations
    def store_document(self, document_data: Dict) -> bool:
        """Store processed document metadata."""
        try:
            with self.get_connection() as conn:
                # Store document
                conn.execute("""
                    INSERT INTO documents
                    (id, file_id, filename, file_type, conversion_method, conversion_time,
                     markdown_content, markdown_storage_path, chunks_storage_path, markdown_length, total_chunks, embeddings_generated,
                     processing_time, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    document_data["document_id"],
                    document_data["file_id"],
                    document_data["filename"],
                    document_data["file_type"],
                    document_data["conversion_method"],
                    document_data.get("conversion_time", 0),
                    document_data.get("markdown_content", ""),
                    document_data.get("markdown_storage_path"),
                    document_data.get("chunks_storage_path"),
                    len(document_data.get("markdown_content", "")),
                    len(document_data.get("chunks", [])),
                    document_data.get("embeddings_generated", False),
                    document_data.get("processing_time", 0),
                    document_data.get("created_at", time.time()),
                    time.time()
                ))
                
                # Store chunks
                chunks = document_data.get("chunks", [])
                if chunks:
                    chunk_data = []
                    for i, chunk in enumerate(chunks):
                        chunk_id = f"{document_data['document_id']}_chunk_{i}"
                        text_preview = chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
                        
                        chunk_data.append((
                            chunk_id,
                            document_data["document_id"],
                            i,
                            chunk["text"],
                            text_preview,
                            chunk.get("start_char", 0),
                            chunk.get("end_char", 0),
                            chunk.get("token_count", 0),
                            "embedding" in chunk,
                            time.time()
                        ))
                    
                    conn.executemany("""
                        INSERT INTO document_chunks 
                        (id, document_id, chunk_index, text, text_preview, start_char, 
                         end_char, token_count, has_embedding, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, chunk_data)
                
                conn.commit()
                logger.info(f"Document stored in database: {document_data['document_id']}")
                return True
        except Exception as e:
            logger.error(f"Error storing document {document_data.get('document_id')}: {str(e)}")
            return False
    
    def get_document(self, document_id: str) -> Optional[Dict]:
        """Get document by ID with chunks."""
        try:
            with self.get_connection() as conn:
                # Get document
                doc_row = conn.execute(
                    "SELECT * FROM documents WHERE id = ?", (document_id,)
                ).fetchone()
                
                if not doc_row:
                    return None
                
                document = dict(doc_row)
                
                # Get chunks
                chunk_rows = conn.execute("""
                    SELECT * FROM document_chunks 
                    WHERE document_id = ? 
                    ORDER BY chunk_index
                """, (document_id,)).fetchall()
                
                document["chunks"] = [dict(row) for row in chunk_rows]
                return document
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {str(e)}")
            return None
    
    def list_documents(self, page: int = 1, page_size: int = 100) -> Dict:
        """List documents with pagination."""
        try:
            offset = (page - 1) * page_size
            
            with self.get_connection() as conn:
                # Get total count
                total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
                
                # Get documents
                rows = conn.execute("""
                    SELECT * FROM documents 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (page_size, offset)).fetchall()
                
                documents = [dict(row) for row in rows]
                
                return {
                    "documents": documents,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return {"documents": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        try:
            with self.get_connection() as conn:
                stats = {}
                
                # File stats
                stats["total_files"] = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
                stats["total_documents"] = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
                stats["total_chunks"] = conn.execute("SELECT COUNT(*) FROM document_chunks").fetchone()[0]
                stats["chunks_with_embeddings"] = conn.execute(
                    "SELECT COUNT(*) FROM document_chunks WHERE has_embedding = 1"
                ).fetchone()[0]
                
                # File type distribution
                file_types = conn.execute("""
                    SELECT file_type, COUNT(*) as count 
                    FROM documents 
                    GROUP BY file_type
                """).fetchall()
                stats["file_types"] = {row[0]: row[1] for row in file_types}
                
                # Database size
                stats["db_size_mb"] = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                
                return stats
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}


# Global service instance
database_service = DatabaseService()
