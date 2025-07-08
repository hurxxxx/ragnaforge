"""
Vector search backend implementations.

This package contains concrete implementations of the VectorSearchInterface
for different vector databases like Qdrant, Milvus, Chroma, etc.
"""

# Import available backends
try:
    from .qdrant_backend import QdrantVectorBackend
    __all__ = ["QdrantVectorBackend"]
except ImportError:
    __all__ = []

# Add other backends as they become available
try:
    from .milvus_backend import MilvusVectorBackend
    __all__.append("MilvusVectorBackend")
except ImportError:
    pass

try:
    from .chroma_backend import ChromaVectorBackend
    __all__.append("ChromaVectorBackend")
except ImportError:
    pass
