# 📄 Document Conversion Performance Comparison Setup

이 가이드는 marker-pdf와 docling을 사용한 PDF 문서 변환 성능 비교 테스트를 위한 설정 방법을 설명합니다.

## 🔧 사전 요구사항

- **CUDA GPU**: GPU 가속을 위해 NVIDIA GPU 필요
- **Python 3.11**: 현재 환경
- **Conda Environment**: `kure-embed-api` 환경 활성화

## 📦 패키지 설치

### 1. 새로운 패키지 설치

```bash
# conda 환경 활성화
conda activate kure-embed-api

# 새로운 패키지 설치
pip install marker-pdf[full] docling
```

### 2. 설치 확인

```bash
# marker 설치 확인
python -c "import marker; print('Marker installed successfully')"

# docling 설치 확인  
python -c "import docling; print('Docling installed successfully')"

# CUDA 확인
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## 🚀 서버 실행

### 1. API 서버 시작

```bash
# 프로젝트 디렉토리에서
/home/edward/miniconda3/envs/kure-embed-api/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. 서버 상태 확인

```bash
curl http://localhost:8000/health
```

## 🧪 테스트 실행

### 1. 기본 성능 비교 테스트

```bash
# 전체 비교 테스트 실행
python tests/test_document_conversion_comparison.py
```

### 2. 개별 API 테스트

#### Marker 변환 테스트
```bash
curl -X POST "http://localhost:8000/v1/convert/marker" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-kure-v1-test-key-12345" \
  -d '{
    "file_path": "sample_docs/P02_01_01_001_20210101.pdf",
    "output_dir": "test_outputs/marker",
    "extract_images": true
  }'
```

#### Docling 변환 테스트
```bash
curl -X POST "http://localhost:8000/v1/convert/docling" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-kure-v1-test-key-12345" \
  -d '{
    "file_path": "sample_docs/P02_01_01_001_20210101.pdf",
    "output_dir": "test_outputs/docling",
    "extract_images": true
  }'
```

#### 직접 비교 테스트
```bash
curl -X POST "http://localhost:8000/v1/convert/compare" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-kure-v1-test-key-12345" \
  -d '{
    "file_path": "sample_docs/P02_01_01_001_20210101.pdf",
    "output_dir": "test_outputs/comparison",
    "extract_images": true
  }'
```

## 📊 결과 분석

### 측정 지표

1. **성능 지표**:
   - 변환 시간 (초)
   - GPU 메모리 사용량 (GB)
   - 처리 속도 비율

2. **출력 품질 지표**:
   - 마크다운 텍스트 길이
   - 추출된 이미지 수
   - 메타데이터 정보

3. **파일 출력**:
   - 마크다운 파일
   - 이미지 파일 (추출된 경우)
   - JSON 결과 파일

### 출력 파일 위치

```
test_outputs/
├── comparison/
│   ├── P02_01_01_001_20210101_marker.md
│   ├── P02_01_01_001_20210101_docling.md
│   ├── P02_01_01_001_20210101_docling.html
│   ├── P02_01_01_001_20210101_docling.json
│   └── comparison_results.json
├── marker/
│   └── P02_01_01_001_20210101_marker.md
└── docling/
    ├── P02_01_01_001_20210101_docling.md
    ├── P02_01_01_001_20210101_docling.html
    └── P02_01_01_001_20210101_docling.json
```

## 🔍 API 엔드포인트

### 1. `/v1/convert/marker` (POST)
- **설명**: Marker를 사용한 PDF 변환
- **입력**: DocumentConversionRequest
- **출력**: DocumentConversionResponse

### 2. `/v1/convert/docling` (POST)
- **설명**: Docling을 사용한 PDF 변환
- **입력**: DocumentConversionRequest
- **출력**: DocumentConversionResponse

### 3. `/v1/convert/compare` (POST)
- **설명**: 두 라이브러리 성능 직접 비교
- **입력**: DocumentConversionRequest
- **출력**: ConversionComparisonResponse

## 🛠️ 문제 해결

### 일반적인 문제들

1. **CUDA 메모리 부족**:
   ```bash
   # GPU 메모리 정리
   python -c "import torch; torch.cuda.empty_cache()"
   ```

2. **패키지 설치 오류**:
   ```bash
   # 패키지 재설치
   pip uninstall marker-pdf docling -y
   pip install marker-pdf[full] docling
   ```

3. **서버 연결 실패**:
   ```bash
   # 포트 확인
   netstat -tlnp | grep 8000
   ```

### 로그 확인

서버 실행 시 로그를 통해 변환 과정을 모니터링할 수 있습니다:

```bash
# 서버 로그에서 변환 진행 상황 확인
# INFO 레벨에서 변환 시작/완료 메시지 출력
# ERROR 레벨에서 오류 정보 출력
```

## 📈 성능 최적화 팁

1. **GPU 메모리 최적화**:
   - 큰 PDF 파일의 경우 배치 크기 조정
   - 불필요한 이미지 추출 비활성화

2. **병렬 처리**:
   - 여러 파일 처리 시 순차 실행 권장
   - GPU 메모리 한계 고려

3. **출력 디렉토리**:
   - SSD 저장소 사용 권장
   - 충분한 디스크 공간 확보

## 🎯 테스트 파일 정보

- **파일**: `sample_docs/P02_01_01_001_20210101.pdf`
- **용도**: 성능 비교 테스트용 샘플 문서
- **특징**: 한국어 문서, 이미지 포함

이 설정을 통해 marker와 docling의 성능을 공정하게 비교하고 각 라이브러리의 장단점을 파악할 수 있습니다.
