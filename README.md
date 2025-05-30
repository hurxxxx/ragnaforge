# KURE v1 API Gateway

KURE (Korea University Retrieval Embedding) 모델을 위한 OpenAI/OpenAPI 호환 REST API 서비스입니다.

## 주요 기능

- **OpenAI 호환**: OpenAI 임베딩 API 형식 및 클라이언트 라이브러리와 완전 호환
- **임베딩 서비스**: 원활한 통합을 위한 OpenAI 호환 임베딩 엔드포인트
- **텍스트 청킹**: 긴 텍스트를 처리 가능한 크기로 자동 분할하는 다양한 전략 제공
- **OpenAPI 3.0 호환**: 대화형 문서가 포함된 완전한 OpenAPI 사양
- **다중 모델 지원**: KURE-v1 및 KoE5 모델 지원
- **RESTful API**: 임베딩, 유사도 계산, 텍스트 청킹을 위한 표준 REST 엔드포인트
- **프로덕션 준비**: 헬스 체크, 로깅, 오류 처리 및 모니터링
- **한국어 최적화**: 한국어 텍스트 처리에 특화

## 빠른 시작

1. **저장소 복제:**
```bash
git clone https://github.com/hurxxxx/kure-v1-api-gateway.git
cd kure-v1-api-gateway
```

2. **의존성 설치:**
```bash
pip install -r requirements.txt
```

3. **환경 설정 (선택사항):**
```bash
cp .env.example .env
# .env 파일을 편집하여 API_KEY 및 기타 설정을 구성
```

4. **서비스 실행:**
```bash
python main.py
```

5. **API 접근:**
- API 기본 URL: http://localhost:8000
- 대화형 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 엔드포인트

### OpenAI 호환 임베딩
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

### OpenAI 클라이언트 라이브러리 사용법

```python
from openai import OpenAI

# OpenAI 클라이언트를 KURE API로 설정
client = OpenAI(
    base_url="http://localhost:8000",
    api_key="sk-kure-v1-your-secret-key"
)

# OpenAI 클라이언트를 사용하여 임베딩 생성
response = client.embeddings.create(
    input=["안녕하세요", "한국어 임베딩 모델입니다"],
    model="nlpai-lab/KURE-v1"
)

embeddings = [data.embedding for data in response.data]
```

### 추가 엔드포인트

#### 임베딩 생성 (대안)
```http
POST /embeddings
```

텍스트 입력에 대한 임베딩을 생성합니다.

**요청 본문:**
```json
{
  "input": ["안녕하세요", "한국어 임베딩 모델입니다"],
  "model": "nlpai-lab/KURE-v1"
}
```

**응답:**
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

### 유사도 계산
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

### 모델 목록
```http
GET /models
```

사용 가능한 모델을 조회합니다.

### 헬스 체크
```http
GET /health
```

서비스 상태를 확인합니다.

### 텍스트 청킹
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

## 설정

`.env.example`을 기반으로 `.env` 파일을 생성하세요:

```bash
cp .env.example .env
```

주요 설정 옵션:
- `DEFAULT_MODEL`: 기본 임베딩 모델 (nlpai-lab/KURE-v1)
- `MAX_BATCH_SIZE`: 요청당 최대 배치 크기 (32)
- `MAX_TEXT_LENGTH`: 최대 텍스트 길이 (8192)
- `API_KEY`: 인증용 Bearer 토큰 (sk-kure-v1-your-secret-key)
- `CACHE_DIR`: 모델 캐시 디렉토리 (./models)
- `LOG_LEVEL`: 로깅 레벨 (INFO)

### 인증

Bearer 토큰 인증을 활성화하려면 `.env` 파일에 `API_KEY`를 설정하세요:

```bash
API_KEY=sk-kure-v1-your-secret-key
```

요청에서 API 키 사용:

```bash
curl -H "Authorization: Bearer sk-kure-v1-your-secret-key" \
     -H "Content-Type: application/json" \
     -d '{"input": "test", "model": "nlpai-lab/KURE-v1"}' \
     http://localhost:8000/embeddings
```

## 사용 가능한 모델

- **nlpai-lab/KURE-v1**: 최신 KURE 모델 (기본값)
- **nlpai-lab/KoE5**: 한국어 E5 모델 (접두사 필요)

## 테스트

실제 API 테스트 실행:
```bash
# 실제 HTTP 요청으로 테스트
python tests/test_real_api.py

# OpenAI 클라이언트 라이브러리로 테스트
python tests/test_real_openai_client.py

# 텍스트 청킹 기능 테스트
python tests/test_chunking.py

# 샘플 문서 청킹 테스트
python tests/test_sample_chunking.py

# 새로운 기본값 테스트
python tests/test_new_defaults.py

# 간단한 테스트 클라이언트
python tests/test_client.py
```

## 프로덕션 배포

프로덕션 배포 시 고려사항:

1. **프로세스 관리**: `systemd`, `supervisor`, 또는 `pm2`와 같은 프로세스 관리자 사용
2. **리버스 프록시**: nginx 또는 Apache를 리버스 프록시로 사용
3. **환경 변수**: 프로덕션 환경 변수 설정
4. **로깅**: 적절한 로깅 및 로그 순환 구성
5. **모니터링**: 헬스 체크 및 모니터링 설정

### uvicorn 예제
```bash
# 다중 워커를 사용한 프로덕션 서버
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API 문서

서비스가 실행되면 다음 주소에서 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 라이선스

MIT License - 자세한 내용은 LICENSE 파일을 참조하세요.

## 인용

```bibtex
@misc{KURE,
  publisher = {Youngjoon Jang, Junyoung Son, Taemin Lee},
  year = {2024},
  url = {https://github.com/nlpai-lab/KURE}
}
```
