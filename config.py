"""
Configuration management for KURE API service.

MIT License - Copyright (c) 2025 hurxxxx
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    app_name: str = "KURE Embedding API"
    app_version: str = "1.0.0"
    app_description: str = "OpenAPI-compatible service for KURE Korean embedding models"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Model Configuration
    default_model: str = "nlpai-lab/KURE-v1"
    available_models: List[str] = [
        "dragonkue/snowflake-arctic-embed-l-v2.0-ko",
        "nlpai-lab/KURE-v1",
        "nlpai-lab/KoE5"
    ]
    cache_dir: Optional[str] = None
    max_sequence_length: int = 512

    # API Limits
    max_batch_size: int = 150
    optimal_batch_size: int = 128
    max_text_length: int = 8192

    # Security
    api_key: Optional[str] = None
    cors_origins: List[str] = ["*"]

    # Logging
    log_level: str = "INFO"

    # Text Chunking Defaults
    default_chunk_strategy: str = "recursive"
    default_chunk_size: int = 380
    default_chunk_overlap: int = 70
    default_chunk_language: str = "auto"

    # OpenAI API Configuration
    openai_api_key: Optional[str] = None

    # GPU Optimization Settings
    gpu_memory_fraction: float = 0.8
    cuda_visible_devices: str = "0"
    torch_cudnn_benchmark: bool = True

    # Qdrant Vector Database Settings
    qdrant_api_key: Optional[str] = None
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "ragnaforge_documents"

    # Search Backend Configuration
    vector_backend: str = "qdrant"  # qdrant, milvus, chroma, weaviate
    text_backend: str = "meilisearch"  # meilisearch, opensearch, elasticsearch, solr

    # MeiliSearch Configuration
    meilisearch_url: str = "http://localhost:7700/"
    meilisearch_api_key: Optional[str] = None
    meilisearch_index_name: str = "ragnaforge_documents"

    # OpenSearch Configuration (for future use)
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_username: Optional[str] = None
    opensearch_password: Optional[str] = None
    opensearch_index_name: str = "ragnaforge_documents"

    # Milvus Configuration (for future use)
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_username: Optional[str] = None
    milvus_password: Optional[str] = None
    milvus_collection_name: str = "ragnaforge_documents"

    # Storage Configuration
    storage_base_path: str = "./data/storage"
    upload_dir: str = "uploads"
    processed_dir: str = "processed"
    temp_dir: str = "temp"
    max_file_size_mb: int = 50

    # Rerank Configuration
    rerank_enabled: bool = True
    rerank_model: str = "dragonkue/bge-reranker-v2-m3-ko"
    rerank_model_type: str = "bge_m3_ko"
    rerank_top_k: int = 100  # Number of documents to rerank from initial search
    rerank_batch_size: int = 32
    rerank_device: Optional[str] = None  # Auto-detect if None
    rerank_cache_enabled: bool = True
    rerank_cache_size: int = 1000  # Number of cached rerank results

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "protected_namespaces": ()
    }


# Global settings instance
settings = Settings()
