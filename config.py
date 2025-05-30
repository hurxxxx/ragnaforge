"""Configuration management for KURE API service."""

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
        "nlpai-lab/KURE-v1",
        "nlpai-lab/KoE5"
    ]
    cache_dir: Optional[str] = None
    max_sequence_length: int = 512

    # API Limits
    max_batch_size: int = 32
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

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "protected_namespaces": ()
    }


# Global settings instance
settings = Settings()
