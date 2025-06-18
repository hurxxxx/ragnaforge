# Ragnaforge

**Ragnaforge**는 문서를 지능적으로 처리하고 검색하는 하이브리드 RAG (Retrieval-Augmented Generation) 시스템입니다. 다양한 문서 형식을 마크다운으로 변환하고, 임베딩을 생성하여 fulltext 검색과 vector 데이터베이스에 저장한 후, 하이브리드 검색을 통해 최적의 결과를 제공합니다.

## 🚀 주요 기능

### 📄 문서 변환
- **다중 형식 지원**: PDF, DOCX, PPTX 등 다양한 문서 형식
- **마크다운 변환**: Marker 및 Docling을 활용한 고품질 마크다운 변환
- **이미지 추출**: 문서 내 이미지 자동 추출 및 저장
- **Self-hosted & Cloud**: 로컬 라이브러리 또는 클라우드 API 선택 가능

### 🧠 임베딩 & 검색
- **로컬/외부 임베딩**: 로컬 모델(KURE-v1, KoE5) 또는 외부 API 지원
- **하이브리드 RAG**: Fulltext 검색 + Vector 검색의 최적 조합
- **Rerank 정확도 향상**: 검색 결과 재순위화로 관련성 극대화
- **한국어 최적화**: 한국어 텍스트 처리에 특화된 성능
- **GPU 가속**: NVIDIA GPU 지원으로 초고속 처리

### 🔌 API 호환성
- **OpenAI 호환**: OpenAI 임베딩 API 형식 및 클라이언트 라이브러리 완전 호환
- **OpenAPI 3.0**: 대화형 문서가 포함된 완전한 OpenAPI 사양
- **MCP 지원**: Model Context Protocol 지원으로 AI 모델과의 원활한 통합
- **RESTful API**: 표준 REST 엔드포인트 제공

### 🌐 확장 가능성
- **웹 크롤링**: 향후 웹 콘텐츠 자동 수집 기능
- **공공 데이터 연계**: 외부 공공 데이터 API와의 통합
- **프로덕션 준비**: 헬스 체크, 로깅, 오류 처리 및 모니터링

## ⚡ 성능 특성

### **RTX 3090 GPU 테스트 결과**
- **문서 변환**: Marker/Docling을 통한 고속 PDF→마크다운 변환
- **임베딩 처리**: 로컬 환경에서 빠른 처리 (50페이지 문서 2.23초)
- **검색 품질**: 한국어 텍스트에서 우수한 유사도 측정 (0.4435 vs 0.3540)
- **비용 효율**: 로컬 처리로 API 호출 비용 없음
- **데이터 보안**: 로컬 처리로 데이터 외부 전송 불필요

### **성능 비교 (50페이지 문서 기준)**
| 모델 | 처리 시간* | 품질 (유사도) | 비용 | 보안 |
|------|-----------|---------------|------|------|
| **KURE v1 (GPU)** | **2.23초** | **0.4435** | **무료** | **로컬** |
| OpenAI Large | 7.2초 | 0.3540 | $0.0044 | 클라우드 |
| OpenAI Small | 9.3초 | 0.3460 | $0.0008 | 클라우드 |

*OpenAI는 네트워크 지연을 포함한 API 호출 시간이며, KURE는 로컬 처리 시간입니다.

### **처리량 비교**
- **KURE v1 (RTX 3090)**: 시간당 1,614개 문서 (로컬)
- **OpenAI Large**: 시간당 500개 문서 (API 호출)
- **CPU 처리**: 시간당 32개 문서 (로컬)

> 📊 **상세 성능 리포트**: [PERFORMANCE_REPORT.md](PERFORMANCE_REPORT.md)

## 🚀 빠른 시작

### 1. 저장소 복제 및 환경 설정
```bash
git clone https://github.com/hurxxxx/ragnaforge.git
cd ragnaforge

# Python 3.11 환경 생성 (권장)
conda create -n ragnaforge python=3.11
conda activate ragnaforge
```

> ⚠️ **중요**: Python 3.11 사용을 강력히 권장합니다. Python 3.13+에서는 일부 패키지 호환성 문제가 발생할 수 있습니다.

### 2. 의존성 설치
```bash
# 기본 의존성 설치
pip install -r requirements.txt

# 문서 변환을 위한 추가 패키지 (선택사항)
pip install marker-pdf[full]  # Marker 지원
pip install docling           # Docling 지원
```

### 3. 환경 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 API_KEY 및 기타 설정을 구성
```

### 4. 서비스 실행
```bash
python main.py
```

### 5. API 접근
- **API 기본 URL**: http://localhost:8000
- **대화형 문서**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 시스템 아키텍처

```
📄 문서 입력 (PDF/DOCX/PPTX)
    ↓
🔄 문서 변환 (Marker/Docling)
    ↓
📝 마크다운 + 이미지 추출
    ↓
✂️ 텍스트 청킹
    ↓
🧠 임베딩 생성 (KURE-v1/KoE5)
    ↓
💾 저장 (Fulltext DB + Vector DB)
    ↓
🔍 하이브리드 RAG 검색
    ↓
🎯 Rerank (정확도 향상)
    ↓
📊 결과 반환
```

## 🔌 API 엔드포인트

### 📄 문서 변환
```http
POST /convert/document
```

PDF, DOCX, PPTX 파일을 마크다운으로 변환합니다.

**요청:**
```bash
curl -X POST "http://localhost:8000/convert/document" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@document.pdf" \
     -F "converter=marker"  # 또는 "docling"
```

### 🧠 OpenAI 호환 임베딩
```http
POST /embeddings
```

**OpenAI 호환 임베딩 엔드포인트** - OpenAI 클라이언트 라이브러리와 원활하게 작동합니다.

**요청 본문:**
```json
{
  "input": ["안녕하세요", "한국어 임베딩 모델입니다"],
  "model": "nlpai-lab/KURE-v1",
  "encoding_format": "float"
}
```

**응답 (OpenAI 형식):**
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

### 🔍 하이브리드 RAG 검색
```http
POST /search
```

Fulltext 검색과 Vector 검색을 결합한 하이브리드 검색을 수행합니다.

**요청 본문:**
```json
{
  "query": "한국어 자연어 처리에 대해 알려주세요",
  "top_k": 10,
  "search_type": "hybrid",  // "fulltext", "vector", "hybrid"
  "model": "nlpai-lab/KURE-v1",
  "rerank": true,
  "rerank_top_k": 5
}
```

### 🎯 Rerank (정확도 향상)
```http
POST /rerank
```

검색 결과의 관련성을 재평가하여 정확도를 향상시킵니다.

**요청 본문:**
```json
{
  "query": "한국어 자연어 처리에 대해 알려주세요",
  "documents": [
    {
      "id": "doc1",
      "text": "한국어 자연어 처리는...",
      "score": 0.85
    },
    {
      "id": "doc2",
      "text": "자연어 처리 기술은...",
      "score": 0.82
    }
  ],
  "model": "nlpai-lab/KURE-v1"
}
```

**응답:**
```json
{
  "reranked_results": [
    {
      "id": "doc1",
      "text": "한국어 자연어 처리는...",
      "original_score": 0.85,
      "rerank_score": 0.94,
      "final_rank": 1
    }
  ],
  "model": "nlpai-lab/KURE-v1"
}
```

### 🐍 OpenAI 클라이언트 라이브러리 사용법

```python
from openai import OpenAI

# OpenAI 클라이언트를 Ragnaforge API로 설정
client = OpenAI(
    base_url="http://localhost:8000",
    api_key="sk-ragnaforge-your-secret-key"
)

# OpenAI 클라이언트를 사용하여 임베딩 생성
response = client.embeddings.create(
    input=["안녕하세요", "한국어 임베딩 모델입니다"],
    model="nlpai-lab/KURE-v1"
)

embeddings = [data.embedding for data in response.data]
```

### 📊 유사도 계산
```http
POST /similarity
```

텍스트 간의 유사도 행렬을 계산합니다.

**요청 본문:**
```json
{
  "texts": ["첫 번째 텍스트", "두 번째 텍스트"],
  "model": "nlpai-lab/KURE-v1"
}
```

**응답:**
```json
{
  "similarities": [[1.0, 0.85], [0.85, 1.0]],
  "model": "nlpai-lab/KURE-v1"
}
```

### 🔧 시스템 관리
```http
GET /models     # 사용 가능한 모델 목록
GET /health     # 서비스 상태 확인
GET /stats      # 시스템 통계 정보
```

### ✂️ 텍스트 청킹
```http
POST /v1/chunk
```

긴 텍스트를 처리 가능한 크기의 청크로 분할합니다.

**요청 본문:**
```json
{
  "text": "이것은 긴 텍스트입니다. 여러 문장으로 구성되어 있습니다. 청킹 기능을 테스트하기 위한 예제입니다.",
  "strategy": "sentence",
  "chunk_size": 512,
  "overlap": 50,
  "language": "auto"
}
```

**응답:**
```json
{
  "object": "list",
  "data": [
    {
      "text": "이것은 긴 텍스트입니다. 여러 문장으로 구성되어 있습니다.",
      "index": 0,
      "start_char": 0,
      "end_char": 35,
      "token_count": 15
    }
  ],
  "total_chunks": 2,
  "strategy": "sentence",
  "original_length": 65,
  "total_tokens": 28
}
```

**청킹 전략:**
- `sentence`: 문장 단위로 분할 (기본값, 의미 보존)
- `recursive`: 재귀적 분할 (문단 → 문장 → 단어 순)
- `token`: 토큰 기반 분할 (정밀한 토큰 제어)

**언어 지원:**
- `auto`: 자동 감지 (기본값)
- `ko`: 한국어 (KSS 사용)
- `en`: 영어 (NLTK 사용)

## ⚙️ 설정

### 환경 설정 파일
`.env.example`을 기반으로 `.env` 파일을 생성하세요:

```bash
cp .env.example .env
```

### 주요 설정 옵션
- `DEFAULT_MODEL`: 기본 임베딩 모델 (nlpai-lab/KURE-v1)
- `MAX_BATCH_SIZE`: 요청당 최대 배치 크기 (32)
- `MAX_TEXT_LENGTH`: 최대 텍스트 길이 (8192)
- `API_KEY`: 인증용 Bearer 토큰 (sk-ragnaforge-your-secret-key)
- `CACHE_DIR`: 모델 캐시 디렉토리 (./models)
- `LOG_LEVEL`: 로깅 레벨 (INFO)

### 문서 변환 설정
- `MARKER_ENABLED`: Marker 변환기 활성화 (true/false)
- `DOCLING_ENABLED`: Docling 변환기 활성화 (true/false)
- `IMAGE_EXTRACT_DIR`: 추출된 이미지 저장 디렉토리
- `CONVERTED_DOCS_DIR`: 변환된 마크다운 파일 저장 디렉토리

### 데이터베이스 설정
- `FULLTEXT_DB_URL`: Fulltext 검색 데이터베이스 URL
- `VECTOR_DB_URL`: Vector 데이터베이스 URL
- `HYBRID_SEARCH_WEIGHTS`: 하이브리드 검색 가중치 설정

### Rerank 설정
- `RERANK_ENABLED`: Rerank 기능 활성화 (true/false)
- `RERANK_MODEL`: Rerank 모델 설정 (nlpai-lab/KURE-v1)
- `RERANK_TOP_K`: Rerank 후 반환할 최대 결과 수 (5)
- `RERANK_THRESHOLD`: Rerank 점수 임계값 (0.7)

### 🔐 인증

Bearer 토큰 인증을 활성화하려면 `.env` 파일에 `API_KEY`를 설정하세요:

```bash
API_KEY=sk-ragnaforge-your-secret-key
```

요청에서 API 키 사용:

```bash
curl -H "Authorization: Bearer sk-ragnaforge-your-secret-key" \
     -H "Content-Type: application/json" \
     -d '{"input": "test", "model": "nlpai-lab/KURE-v1"}' \
     http://localhost:8000/embeddings
```

## 🤖 사용 가능한 모델

### 임베딩 모델
- **nlpai-lab/KURE-v1**: 최신 KURE 모델 (기본값, 한국어 최적화)
- **nlpai-lab/KoE5**: 한국어 E5 모델 (접두사 필요)

### 문서 변환 도구
- **Marker**: 고속 PDF 변환, 수식 및 표 지원
- **Docling**: 다중 형식 지원, 고품질 레이아웃 보존

## 💻 시스템 요구사항

### Python 버전
- **Python 3.11** (강력히 권장)
- Python 3.10 (지원됨)
- Python 3.12 (대부분 지원됨)
- ⚠️ Python 3.13+ (일부 패키지 호환성 문제 가능)

### 하드웨어 요구사항
- **메모리**: 최소 8GB RAM (16GB 권장)
- **저장공간**: 10GB+ 여유 공간
- **GPU**: NVIDIA GPU (선택사항, 성능 향상)
  - RTX 3090: 최적 성능
  - RTX 4090: 최고 성능
  - CUDA 11.8+ 지원

### 운영체제
- Linux (Ubuntu 20.04+ 권장)
- macOS (Intel/Apple Silicon)
- Windows 10/11

## 🧪 테스트

```bash
# API 기본 기능 테스트
python tests/test_real_api.py

# 문서 변환 성능 비교
python tests/test_document_conversion_comparison.py
```

## 📚 API 문서

서비스 실행 후 다음 주소에서 확인:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📄 라이선스

MIT License

---

**Ragnaforge** - 차세대 하이브리드 RAG 시스템으로 문서를 지능적으로 처리하고 검색하세요.
