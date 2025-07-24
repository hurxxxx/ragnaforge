# 데이터 초기화 스크립트 사용법

이 문서는 RagnaForge 프로젝트의 모든 데이터를 초기화하는 방법을 설명합니다.

## 🚨 주의사항

**⚠️ 이 스크립트들은 모든 데이터를 영구적으로 삭제합니다!**
- 업로드된 문서 파일
- 처리된 문서 데이터
- 벡터 임베딩 데이터 (Qdrant)
- 전문 검색 인덱스 (MeiliSearch)
- 캐시된 모델 파일
- 임시 파일들

**백업이 필요한 데이터가 있다면 먼저 백업하세요!**

## 📋 초기화 옵션

### 1. 완전 초기화 (권장)
모든 데이터를 초기화하고 깨끗한 상태로 시작

```bash
# Python 스크립트 실행 (Qdrant + MeiliSearch + 로컬 파일)
python reset_all_data.py
```

### 2. 로컬 파일만 초기화
원격 데이터베이스는 그대로 두고 로컬 파일만 정리

```bash
# Bash 스크립트 실행 (로컬 파일만)
./reset_data_simple.sh
```

## 🔧 스크립트 상세 설명

### `reset_all_data.py` (완전 초기화)

**초기화 대상:**
- ✅ Qdrant 컬렉션 삭제 및 재생성
- ✅ MeiliSearch 인덱스 삭제 및 재생성  
- ✅ 로컬 스토리지 파일 삭제
- ✅ 캐시 파일 정리
- ✅ 초기화 결과 검증

**필요한 의존성:**
```bash
pip install qdrant-client meilisearch python-dotenv httpx
```

**실행 과정:**
1. 사용자 확인 (2단계)
2. Qdrant 컬렉션 초기화
3. MeiliSearch 인덱스 초기화
4. 로컬 스토리지 정리
5. 캐시 파일 정리
6. 결과 검증

### `reset_data_simple.sh` (로컬만 초기화)

**초기화 대상:**
- ✅ 로컬 스토리지 파일 삭제 (`./data/`)
- ✅ 모델 캐시 삭제 (`./models/`)
- ✅ Python 캐시 정리 (`__pycache__`, `*.pyc`)
- ✅ 스토리지 디렉토리 재생성

**장점:**
- Python 의존성 불필요
- 빠른 실행
- 원격 DB는 보존

## 📁 초기화되는 디렉토리

```
ragnaforge/
├── data/                    # 전체 데이터 디렉토리
│   └── storage/
│       ├── uploads/         # 업로드된 원본 파일
│       ├── processed/       # 처리된 문서 데이터
│       └── temp/           # 임시 파일
├── models/                  # 캐시된 AI 모델
└── __pycache__/            # Python 캐시 파일
```

## 🔄 초기화 후 작업

초기화 완료 후 다음 단계를 진행하세요:

1. **서버 재시작**
   ```bash
   # 기존 서버 종료 후
   python main.py
   ```

2. **Streamlit 재시작**
   ```bash
   streamlit run streamlit_app.py
   ```

3. **새 문서 업로드**
   - Streamlit UI에서 문서 업로드
   - 또는 API를 통한 문서 업로드

## 🛠️ 환경 설정 확인

초기화 스크립트는 `.env` 파일의 설정을 사용합니다:

```env
# Qdrant 설정
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=your-qdrant-api-key

# MeiliSearch 설정
MEILISEARCH_URL=http://localhost:7700/
MEILISEARCH_API_KEY=your-meilisearch-api-key

# 스토리지 설정
STORAGE_BASE_PATH=./data/storage
UPLOAD_DIR=uploads
PROCESSED_DIR=processed
TEMP_DIR=temp
```

## 🐛 문제 해결

### 권한 오류
```bash
chmod +x reset_data_simple.sh
```

### Python 의존성 오류
```bash
pip install -r requirements.txt
```

### 원격 DB 연결 오류
- `.env` 파일의 API 키와 URL 확인
- 네트워크 연결 상태 확인
- 방화벽 설정 확인

### 부분 실패 시
스크립트가 부분적으로 실패한 경우:
1. 로그 메시지 확인
2. 수동으로 남은 데이터 정리
3. 스크립트 재실행

## 📞 지원

문제가 발생하면:
1. 로그 메시지 확인
2. `.env` 설정 검증
3. 네트워크 연결 확인
4. 필요시 수동 정리 후 재시도

---

**⚠️ 다시 한 번 주의: 이 작업은 되돌릴 수 없습니다!**
