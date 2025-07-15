# Ragnaforge

**Ragnaforge**는 문서를 지능적으로 처리하고 검색하는 하이브리드 RAG (Retrieval-Augmented Generation) 시스템입니다. 다양한 문서 형식을 마크다운으로 변환하고, 임베딩을 생성하여 Vector 검색과 Text 검색을 결합한 하이브리드 검색을 제공합니다.

## 🚀 주요 기능

### 📄 문서 처리
- **다중 형식 지원**: PDF, DOCX, PPTX, MD, TXT
- **마크다운 변환**: Marker 기본 지원 (고품질 변환), Docling 선택 지원
- **통합 처리 API**: 업로드부터 벡터 저장까지 원스톱 처리
- **이미지 추출**: 문서 내 이미지 자동 추출 및 저장
- **체계적 저장**: 파일 타입별 자동 분류 및 메타데이터 관리
- **중복 문서 관리**: 파일 해시 기반 중복 검사 및 자동 처리

### 🧠 임베딩 & 검색
- **로컬 임베딩**: KURE-v1 (1024차원), KoE5 모델 지원
- **하이브리드 검색**: Vector 검색 + Text 검색 결합
- **리랭킹 시스템**: BGE Cross-encoder 기반 검색 결과 품질 향상
- **한국어 최적화**: 한국어 텍스트 처리 특화
- **GPU 가속**: NVIDIA GPU 지원으로 고속 처리
- **실시간 성능**: 벡터 검색 0.2-1.3초, 하이브리드 검색 0.2-0.4초

### 🔌 API 호환성
- **OpenAI 호환**: OpenAI 임베딩 API 형식 완전 호환
- **OpenAPI 3.0**: 대화형 문서 포함
- **RESTful API**: 표준 REST 엔드포인트 제공

## 🚀 빠른 시작

### 1. 저장소 복제 및 환경 설정
```bash
git clone https://github.com/hurxxxx/ragnaforge.git
cd ragnaforge

# Python 3.11 환경 생성 (권장)
conda create -n ragnaforge python=3.11
conda activate ragnaforge
```

### 2. 설치 방법

#### 방법 1: PyPI에서 설치 (권장)
```bash
# 기본 설치
pip install ragnaforge

# 모든 기능 포함 설치
pip install ragnaforge[all]

# 특정 기능만 설치
pip install ragnaforge[marker]  # Marker 지원
pip install ragnaforge[docling] # Docling 지원
```

#### 방법 2: 소스에서 설치
```bash
# 기본 의존성 설치
pip install -r requirements.txt

# 문서 변환을 위한 추가 패키지 (선택사항)
pip install marker-pdf[full]  # Marker 지원
pip install docling           # Docling 지원

# 개발 모드로 설치
pip install -e .
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
- **API 문서**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 주요 API 엔드포인트

### 📄 파일 업로드 및 처리
```http
POST /v1/upload_and_process  # 통합 업로드+처리 (권장)
POST /v1/upload              # 파일 업로드만
POST /v1/process             # 문서 처리 및 임베딩 생성
```

### 🧠 임베딩 API (OpenAI 호환)
```http
POST /embeddings       # 텍스트 임베딩 생성
POST /similarity       # 텍스트 유사도 계산
```

### 🔍 검색 API
```http
POST /v1/search/vector    # 벡터 검색 (리랭킹 지원)
POST /v1/search/text      # 텍스트 검색 (하이라이트 지원)
POST /v1/search/hybrid    # 하이브리드 검색 (가중치 조절)
POST /v1/rerank           # 리랭킹 전용 API
```

### 🔧 시스템 관리
```http
GET /health               # 서비스 상태 확인
GET /models               # 사용 가능한 모델 목록
GET /v1/storage/stats     # 저장소 통계
GET /v1/files             # 업로드된 파일 목록
GET /v1/rerank/health     # 리랭킹 서비스 상태
```

### 🚀 통합 업로드 API 사용 예제

```bash
# 파일 업로드와 처리를 한 번에 수행
curl -X POST "http://localhost:8000/v1/upload_and_process" \
  -H "Authorization: Bearer your-api-key" \
  -F "file=@document.pdf" \
  -F "conversion_method=auto" \
  -F "generate_embeddings=true"
```

### 🔍 검색 API 사용 예제

```bash
# 하이브리드 검색 (리랭킹 적용)
curl -X POST "http://localhost:8000/v1/search/hybrid" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "인공지능 기술",
    "vector_weight": 0.7,
    "text_weight": 0.3,
    "limit": 5,
    "rerank": true
  }'
```

### 🐍 OpenAI 클라이언트 사용 예제

```python
from openai import OpenAI

# Ragnaforge API 설정
client = OpenAI(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# 임베딩 생성
response = client.embeddings.create(
    input=["안녕하세요", "한국어 임베딩 테스트"],
    model="nlpai-lab/KURE-v1"
)
```

## ⚙️ 환경 설정

### 기본 설정
`.env.example`을 복사하여 `.env` 파일을 생성하고 필요한 설정을 수정하세요:

```bash
cp .env.example .env
```

### 주요 설정 옵션
- `API_KEY`: 인증용 Bearer 토큰
- `DEFAULT_MODEL`: 기본 임베딩 모델 (nlpai-lab/KURE-v1)
- `STORAGE_BASE_PATH`: 파일 저장 경로 (./data/storage)
- `MAX_FILE_SIZE_MB`: 최대 파일 크기 (50MB)
- `LOG_LEVEL`: 로깅 레벨 (INFO)

## 🤖 지원 모델 및 기술 스택

### 임베딩 모델
- **nlpai-lab/KURE-v1**: 한국어 최적화 모델 (기본값, 1024차원)
- **nlpai-lab/KoE5**: 한국어 E5 모델

### 문서 변환
- **Marker**: 고속 PDF/DOCX/PPTX 변환 (기본값)
- **Docling**: 다중 형식 지원 (선택사항)

### 검색 엔진
- **Qdrant**: 벡터 데이터베이스
- **MeiliSearch**: 전문 검색 엔진

### 리랭킹 모델
- **dragonkue/bge-reranker-v2-m3-ko**: 한국어 특화 Cross-encoder

## 💻 시스템 요구사항

### Python 버전
- **Python 3.11** (강력히 권장)
- Python 3.10+ (지원됨)

### 하드웨어 요구사항
- **메모리**: 최소 8GB RAM (16GB 권장)
- **저장공간**: 10GB+ 여유 공간
- **GPU**: NVIDIA GPU (선택사항, 성능 향상)

### 운영체제
- Linux (Ubuntu 20.04+ 권장)
- macOS (Intel/Apple Silicon)
- Windows 10/11

## 📊 성능 지표

### 처리 성능
- **파일 업로드+처리**: ~45초 (전체 파이프라인)
- **벡터 검색**: 0.2-1.3초 응답 시간
- **하이브리드 검색**: 0.2-0.4초 응답 시간
- **리랭킹**: 3-53초 (품질 향상)

### 지원 기능
- **문서 형식**: PDF, DOCX, PPTX, MD, TXT
- **최대 파일 크기**: 50MB
- **동시 처리**: 멀티스레드 지원
- **중복 검사**: SHA-256 해시 기반

## 📚 API 문서

서비스 실행 후 다음 주소에서 확인:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 테스트

### 종합 테스트 실행
```bash
# 완전한 파이프라인 테스트
./test_complete_pipeline.sh

# 모든 검색 타입 테스트 (82개 테스트 케이스)
./test_comprehensive_search_test.sh
```

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

### MIT 라이선스 주요 내용:
- ✅ **상업적 사용 허용**: 상업적 목적으로 자유롭게 사용 가능
- ✅ **수정 및 배포 허용**: 소스 코드 수정 및 재배포 가능
- ✅ **사적 사용 허용**: 개인적 용도로 자유롭게 사용 가능
- ✅ **특허 사용 허용**: 특허권 행사 제한 없음
- ⚠️ **라이선스 및 저작권 고지 필수**: 라이선스 텍스트와 저작권 고지 포함 필요
- ❌ **보증 없음**: 소프트웨어에 대한 어떠한 보증도 제공하지 않음

---

**Ragnaforge** - 하이브리드 RAG 시스템으로 문서를 지능적으로 처리하고 검색하세요.