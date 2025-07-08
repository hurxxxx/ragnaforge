"""
Search backend interfaces for Ragnaforge.

This module defines abstract interfaces for vector and text search backends,
enabling easy switching between different search engines (Qdrant/Milvus, MeiliSearch/OpenSearch).
"""

from .vector_search_interface import VectorSearchInterface
from .text_search_interface import TextSearchInterface

__all__ = [
    "VectorSearchInterface",
    "TextSearchInterface"
]
