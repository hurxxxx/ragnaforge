"""
Setup script for Ragnaforge.

MIT License - Copyright (c) 2025 hurxxxx
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ragnaforge",
    version="1.0.0",
    author="hurxxxx",
    author_email="hurxxxx@gmail.com",
    description="Hybrid RAG system for intelligent document processing and search",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hurxxxx/ragnaforge",
    project_urls={
        "Bug Tracker": "https://github.com/hurxxxx/ragnaforge/issues",
        "Documentation": "https://github.com/hurxxxx/ragnaforge#readme",
        "Source Code": "https://github.com/hurxxxx/ragnaforge",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "marker": [
            "marker-pdf[full]",
        ],
        "docling": [
            "docling",
        ],
        "all": [
            "marker-pdf[full]",
            "docling",
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ragnaforge=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml", "*.json"],
    },
    keywords=[
        "rag",
        "retrieval-augmented-generation",
        "document-processing",
        "vector-search",
        "hybrid-search",
        "embedding",
        "korean-nlp",
        "fastapi",
        "qdrant",
        "meilisearch",
    ],
    license="MIT",
    zip_safe=False,
)
