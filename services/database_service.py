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
                    upload_time REAL NOT NULL,
                    created_at REAL NOT NULL,
                    status TEXT DEFAULT 'uploaded'
                )
            """)
            
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
                    markdown_length INTEGER NOT NULL,
                    total_chunks INTEGER NOT NULL,
                    embeddings_generated BOOLEAN NOT NULL,
                    processing_time REAL NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            """)
            
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
                    (id, filename, safe_filename, file_type, file_size, temp_path, upload_time, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_data["file_id"],
                    file_data["filename"],
                    file_data["safe_filename"],
                    file_data["file_type"],
                    file_data["file_size"],
                    file_data["temp_path"],
                    file_data["upload_time"],
                    file_data["created_at"]
                ))
                conn.commit()
                logger.info(f"File stored in database: {file_data['file_id']}")
                return True
        except Exception as e:
            logger.error(f"Error storing file {file_data.get('file_id')}: {str(e)}")
            return False
    
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
                     markdown_content, markdown_length, total_chunks, embeddings_generated,
                     processing_time, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    document_data["document_id"],
                    document_data["file_id"],
                    document_data["filename"],
                    document_data["file_type"],
                    document_data["conversion_method"],
                    document_data.get("conversion_time", 0),
                    document_data.get("markdown_content", ""),
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
