"""
MeiliSearch text search backend implementation.

This module provides a concrete implementation of the TextSearchInterface
for MeiliSearch search engine.
"""

import logging
import time
from typing import Dict, List, Optional, Any
import meilisearch
from meilisearch.errors import MeilisearchError

from ..interfaces.text_search_interface import TextSearchInterface
from config import settings

logger = logging.getLogger(__name__)


class MeiliSearchTextBackend(TextSearchInterface):
    """MeiliSearch implementation of text search backend."""
    
    def __init__(self):
        self.client = None
        self.index_name = settings.meilisearch_index_name
        self.index = None
        self._connected = False
        logger.info("MeiliSearch text backend initialized")
    
    async def initialize(self) -> bool:
        """Initialize the MeiliSearch client and connection."""
        try:
            # Initialize client
            self.client = meilisearch.Client(
                url=settings.meilisearch_url,
                api_key=settings.meilisearch_api_key
            )
            
            # Test connection
            health = self.client.health()
            logger.info(f"Connected to MeiliSearch: {health}")
            
            # Get or create index
            try:
                self.index = self.client.get_index(self.index_name)
                logger.info(f"Using existing MeiliSearch index: {self.index_name}")
            except MeilisearchError:
                # Index doesn't exist, create it
                await self.create_index(self.index_name)
                self.index = self.client.get_index(self.index_name)
                logger.info(f"Created new MeiliSearch index: {self.index_name}")
            
            # Configure index settings for Korean text
            await self._configure_korean_settings()
            
            self._connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MeiliSearch client: {str(e)}")
            self._connected = False
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check MeiliSearch health status."""
        try:
            if not self.client:
                return {"status": "disconnected", "error": "Client not initialized"}
            
            health = self.client.health()
            stats = self.index.get_stats() if self.index else {}
            
            return {
                "status": "healthy",
                "backend": "meilisearch",
                "url": settings.meilisearch_url,
                "index_name": self.index_name,
                "health": health,
                "documents_count": getattr(stats, "number_of_documents", 0),
                "is_indexing": getattr(stats, "is_indexing", False),
                "field_distribution": getattr(stats, "field_distribution", {})
            }
            
        except Exception as e:
            logger.error(f"MeiliSearch health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "backend": "meilisearch",
                "error": str(e)
            }
    
    async def create_index(self, index_name: str, settings_config: Optional[Dict[str, Any]] = None) -> bool:
        """Create a new index in MeiliSearch."""
        try:
            # Create index
            task = self.client.create_index(index_name, {"primaryKey": "id"})
            
            # Wait for task completion
            self.client.wait_for_task(task.task_uid)
            
            logger.info(f"Created MeiliSearch index: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {str(e)}")
            return False
    
    async def _configure_korean_settings(self):
        """Configure MeiliSearch settings optimized for Korean text."""
        try:
            if not self.index:
                return
            
            # Configure searchable attributes
            searchable_attributes = [
                "title",
                "content", 
                "file_name",
                "file_type",
                "metadata"
            ]
            
            # Configure filterable attributes
            filterable_attributes = [
                "document_id",
                "file_type",
                "file_name",
                "created_at",
                "chunk_index",
                "file_size"
            ]
            
            # Configure sortable attributes
            sortable_attributes = [
                "created_at",
                "file_size",
                "chunk_index"
            ]
            
            # Configure typo tolerance for Korean
            typo_tolerance = {
                "enabled": True,
                "minWordSizeForTypos": {
                    "oneTypo": 3,
                    "twoTypos": 5
                },
                "disableOnWords": [],
                "disableOnAttributes": []
            }
            
            # Apply settings
            settings_update = {
                "searchableAttributes": searchable_attributes,
                "filterableAttributes": filterable_attributes,
                "sortableAttributes": sortable_attributes,
                "typoTolerance": typo_tolerance,
                "pagination": {
                    "maxTotalHits": 10000
                }
            }
            
            task = self.index.update_settings(settings_update)
            self.client.wait_for_task(task.task_uid)
            
            logger.info("Configured MeiliSearch settings for Korean text")
            
        except Exception as e:
            logger.error(f"Failed to configure Korean settings: {str(e)}")
    
    async def index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Index documents for text search."""
        try:
            if not documents:
                logger.warning("No documents provided for indexing")
                return True
            
            if not self.index:
                logger.error("Index not initialized")
                return False
            
            # Prepare documents for MeiliSearch
            prepared_docs = []
            for doc in documents:
                if 'id' not in doc:
                    logger.warning(f"Document missing required 'id' field: {doc}")
                    continue
                
                # Prepare document with required fields
                prepared_doc = {
                    "id": doc['id'],
                    "title": doc.get('title', ''),
                    "content": doc.get('content', ''),
                    "file_name": doc.get('file_name', ''),
                    "file_type": doc.get('file_type', ''),
                    "created_at": doc.get('created_at', time.time()),
                    "chunk_index": doc.get('chunk_index', 0),
                    "file_size": doc.get('file_size', 0),
                    "document_id": doc.get('document_id', doc['id'])
                }
                
                # Add metadata fields
                if 'metadata' in doc:
                    prepared_doc.update(doc['metadata'])
                
                prepared_docs.append(prepared_doc)
            
            if not prepared_docs:
                logger.warning("No valid documents to index")
                return True
            
            # Index documents
            task = self.index.add_documents(prepared_docs)
            self.client.wait_for_task(task.task_uid)
            
            logger.info(f"Indexed {len(prepared_docs)} documents in MeiliSearch")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing documents in MeiliSearch: {str(e)}")
            return False
    
    async def search_text(self, 
                         query: str, 
                         limit: int = 10,
                         offset: int = 0,
                         filters: Optional[Dict[str, Any]] = None,
                         sort: Optional[List[str]] = None,
                         highlight: bool = False) -> Dict[str, Any]:
        """Search for documents using text query."""
        try:
            if not self.index:
                logger.error("Index not initialized")
                return {"hits": [], "total": 0, "query": query}
            
            # Prepare search options
            search_options = {
                "limit": limit,
                "offset": offset,
                "attributesToRetrieve": ["*"],
                "attributesToHighlight": ["title", "content"] if highlight else [],
                "highlightPreTag": "<mark>",
                "highlightPostTag": "</mark>",
                "cropLength": 200,
                "showMatchesPosition": False
            }
            
            # Add filters if provided
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if isinstance(value, list):
                        # Multiple values - use IN operator
                        values_str = " OR ".join([f'"{v}"' for v in value])
                        filter_conditions.append(f"{key} IN [{values_str}]")
                    else:
                        filter_conditions.append(f'{key} = "{value}"')
                
                if filter_conditions:
                    search_options["filter"] = " AND ".join(filter_conditions)
            
            # Add sorting if provided
            if sort:
                search_options["sort"] = sort
            
            # Perform search
            search_results = self.index.search(query, search_options)
            
            # Format results
            formatted_results = {
                "hits": search_results.get("hits", []),
                "total": search_results.get("estimatedTotalHits", 0),
                "query": query,
                "processing_time_ms": search_results.get("processingTimeMs", 0),
                "limit": limit,
                "offset": offset
            }
            
            logger.info(f"Found {len(formatted_results['hits'])} text search results for query: '{query[:50]}...'")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching text in MeiliSearch: {str(e)}")
            return {"hits": [], "total": 0, "query": query, "error": str(e)}

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document from MeiliSearch."""
        try:
            if not self.index:
                logger.error("Index not initialized")
                return False

            task = self.index.delete_document(document_id)
            self.client.wait_for_task(task.task_uid)

            logger.info(f"Deleted document {document_id} from MeiliSearch")
            return True

        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False

    async def delete_index(self, index_name: str) -> bool:
        """Delete an entire index."""
        try:
            task = self.client.delete_index(index_name)
            self.client.wait_for_task(task.task_uid)

            logger.info(f"Deleted index: {index_name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting index {index_name}: {str(e)}")
            return False

    async def update_document(self, document_id: str, document: Dict[str, Any]) -> bool:
        """Update a document in MeiliSearch."""
        try:
            if not self.index:
                logger.error("Index not initialized")
                return False

            # Ensure document has ID
            document["id"] = document_id

            task = self.index.update_documents([document])
            self.client.wait_for_task(task.task_uid)

            logger.info(f"Updated document {document_id} in MeiliSearch")
            return True

        except Exception as e:
            logger.error(f"Error updating document {document_id}: {str(e)}")
            return False

    async def suggest(self, query: str, limit: int = 5) -> List[str]:
        """Get search suggestions for a query."""
        try:
            if not self.index:
                logger.error("Index not initialized")
                return []

            # MeiliSearch doesn't have built-in suggestions,
            # so we'll do a search and extract unique terms
            search_results = self.index.search(query, {
                "limit": limit * 2,
                "attributesToRetrieve": ["title", "content"],
                "cropLength": 50
            })

            suggestions = set()
            for hit in search_results.get("hits", []):
                title = hit.get("title", "")
                content = hit.get("content", "")

                # Extract words that start with the query
                words = (title + " " + content).lower().split()
                for word in words:
                    if word.startswith(query.lower()) and len(word) > len(query):
                        suggestions.add(word)
                        if len(suggestions) >= limit:
                            break

                if len(suggestions) >= limit:
                    break

            return list(suggestions)[:limit]

        except Exception as e:
            logger.error(f"Error getting suggestions: {str(e)}")
            return []

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific document by ID."""
        try:
            if not self.index:
                logger.error("Index not initialized")
                return None

            document = self.index.get_document(document_id)
            return document

        except Exception as e:
            logger.error(f"Error getting document {document_id}: {str(e)}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get MeiliSearch statistics."""
        try:
            if not self.index:
                return {"backend": "meilisearch", "error": "Index not initialized"}

            stats = self.index.get_stats()
            settings = self.index.get_settings()

            return {
                "backend": "meilisearch",
                "index_name": self.index_name,
                "documents_count": getattr(stats, "number_of_documents", 0),
                "is_indexing": getattr(stats, "is_indexing", False),
                "field_distribution": dict(getattr(stats, "field_distribution", {})),
                "searchable_attributes": getattr(settings, "searchable_attributes", []),
                "filterable_attributes": getattr(settings, "filterable_attributes", []),
                "sortable_attributes": getattr(settings, "sortable_attributes", [])
            }

        except Exception as e:
            logger.error(f"Error getting MeiliSearch stats: {str(e)}")
            return {"backend": "meilisearch", "error": str(e)}

    async def batch_search(self,
                         queries: List[str],
                         limit: int = 10,
                         filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Perform batch text search for multiple queries."""
        try:
            if not self.index:
                logger.error("Index not initialized")
                return [{"hits": [], "total": 0, "query": q} for q in queries]

            # MeiliSearch doesn't have native batch search, so we'll do sequential searches
            results = []
            for query in queries:
                result = await self.search_text(query, limit=limit, filters=filters)
                results.append(result)

            logger.info(f"Completed batch search for {len(queries)} queries")
            return results

        except Exception as e:
            logger.error(f"Error in batch search: {str(e)}")
            return [{"hits": [], "total": 0, "query": q, "error": str(e)} for q in queries]

    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text using MeiliSearch's analyzer."""
        try:
            # MeiliSearch doesn't expose text analysis API directly
            # We'll simulate by doing a search and seeing how it's processed
            if not self.index:
                return {"error": "Index not initialized"}

            # This is a simplified analysis - in a real implementation,
            # you might want to use external tokenizers
            words = text.lower().split()

            return {
                "original_text": text,
                "tokens": words,
                "token_count": len(words),
                "analyzer": "meilisearch_default"
            }

        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
            return {"error": str(e)}

    @property
    def backend_name(self) -> str:
        """Return the backend name."""
        return "meilisearch"

    @property
    def is_connected(self) -> bool:
        """Return connection status."""
        return self._connected and self.client is not None
