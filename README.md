# KURE v1 API Gateway

OpenAI/OpenAPI compatible REST API service for KURE (Korea University Retrieval Embedding) models.

## Features

- **OpenAI Compatible**: Full compatibility with OpenAI embeddings API format and client libraries
- **Embeddings**: OpenAI-compatible embeddings endpoint for seamless integration
- **OpenAPI 3.0 Compatible**: Full OpenAPI specification with interactive documentation
- **Multiple Models**: Support for KURE-v1 and KoE5 models
- **RESTful API**: Standard REST endpoints for embedding and similarity operations
- **Docker Support**: Containerized deployment with Docker and Docker Compose
- **Production Ready**: Health checks, logging, error handling, and monitoring
- **Korean Language Optimized**: Specialized for Korean text processing

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd kure-v1-wrapper
```

2. Start the service:
```bash
docker-compose up -d
```

3. Access the API:
- API Base URL: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
python main.py
```

## API Endpoints

### OpenAI Compatible Embeddings
```http
POST /embeddings
```

**OpenAI-compatible embeddings endpoint** - works seamlessly with OpenAI client libraries.

**Request Body:**
```json
{
  "input": ["안녕하세요", "한국어 임베딩 모델입니다"],
  "model": "nlpai-lab/KURE-v1",
  "encoding_format": "float"
}
```

**Response (OpenAI Format):**
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.1, 0.2, ...],
      "index": 0
    }
  ],
  "model": "nlpai-lab/KURE-v1",
  "usage": {
    "prompt_tokens": 10,
    "total_tokens": 10
  }
}
```

### Using with OpenAI Client Library

```python
from openai import OpenAI

# Point OpenAI client to KURE API
client = OpenAI(
    base_url="http://localhost:8000",
    api_key="sk-kure-v1-your-secret-key"
)

# Generate embeddings using OpenAI client
response = client.embeddings.create(
    input=["안녕하세요", "한국어 임베딩 모델입니다"],
    model="nlpai-lab/KURE-v1"
)

embeddings = [data.embedding for data in response.data]
```

### Additional Endpoints

#### Generate Embeddings (Alternative)
```http
POST /embeddings
```

Generate embeddings for text inputs.

**Request Body:**
```json
{
  "input": ["안녕하세요", "한국어 임베딩 모델입니다"],
  "model": "nlpai-lab/KURE-v1"
}
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.1, 0.2, ...],
      "index": 0
    }
  ],
  "model": "nlpai-lab/KURE-v1",
  "usage": {
    "prompt_tokens": 10,
    "total_tokens": 10
  }
}
```

### Calculate Similarity
```http
POST /similarity
```

Calculate similarity matrix between texts.

**Request Body:**
```json
{
  "texts": ["첫 번째 텍스트", "두 번째 텍스트"],
  "model": "nlpai-lab/KURE-v1"
}
```

**Response:**
```json
{
  "similarities": [[1.0, 0.85], [0.85, 1.0]],
  "model": "nlpai-lab/KURE-v1"
}
```

### List Models
```http
GET /models
```

Get available models.

### Health Check
```http
GET /health
```

Service health status.

## Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Key configuration options:
- `DEFAULT_MODEL`: Default embedding model (nlpai-lab/KURE-v1)
- `MAX_BATCH_SIZE`: Maximum batch size for requests (32)
- `MAX_TEXT_LENGTH`: Maximum text length (8192)
- `API_KEY`: Bearer token for authentication (sk-kure-v1-your-secret-key)
- `CACHE_DIR`: Model cache directory (./models)
- `LOG_LEVEL`: Logging level (INFO)

### Authentication

Set `API_KEY` in your `.env` file to enable Bearer token authentication:

```bash
API_KEY=sk-kure-v1-your-secret-key
```

Use the API key in requests:

```bash
curl -H "Authorization: Bearer sk-kure-v1-your-secret-key" \
     -H "Content-Type: application/json" \
     -d '{"input": "test", "model": "nlpai-lab/KURE-v1"}' \
     http://localhost:8000/embeddings
```

## Available Models

- **nlpai-lab/KURE-v1**: Latest KURE model (default)
- **nlpai-lab/KoE5**: Korean E5 model (requires prefix)

## Testing

Run real API tests:
```bash
# Test with real HTTP requests
python test_real_api.py

# Test with OpenAI client library
python test_real_openai_client.py

# Simple test client
python scripts/test_client.py
```

## Production Deployment

### Docker
```bash
docker build -t kure-api .
docker run -p 8000:8000 kure-api
```

### Docker Compose
```bash
docker-compose up -d
```

## API Documentation

Once the service is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## License

MIT License - see LICENSE file for details.

## Citation

```bibtex
@misc{KURE,
  publisher = {Youngjoon Jang, Junyoung Son, Taemin Lee},
  year = {2024},
  url = {https://github.com/nlpai-lab/KURE}
}
```
