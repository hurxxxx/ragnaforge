"""
Text search backend implementations.

This package contains concrete implementations of the TextSearchInterface
for different search engines like MeiliSearch, OpenSearch, Elasticsearch, etc.
"""

# Import available backends
try:
    from .meilisearch_backend import MeiliSearchTextBackend
    __all__ = ["MeiliSearchTextBackend"]
except ImportError:
    __all__ = []

# Add other backends as they become available
try:
    from .opensearch_backend import OpenSearchTextBackend
    __all__.append("OpenSearchTextBackend")
except ImportError:
    pass

try:
    from .elasticsearch_backend import ElasticsearchTextBackend
    __all__.append("ElasticsearchTextBackend")
except ImportError:
    pass
