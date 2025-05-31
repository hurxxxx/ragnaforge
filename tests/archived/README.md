# 아카이브된 테스트 파일

이 디렉토리에는 특수한 목적이나 성능 비교를 위한 테스트 파일들이 보관되어 있습니다.

## 성능 비교 테스트

### `test_performance_comparison.py`
- OpenAI vs KURE v1 성능 비교
- 유사도 측정 및 처리 시간 비교
- 실행: `python tests/archived/test_performance_comparison.py`

### `test_real_document_performance.py`
- 실제 문서 기반 성능 테스트
- 대용량 문서 처리 성능 측정
- 실행: `python tests/archived/test_real_document_performance.py`

### `test_openai_vs_kure_real_document.py`
- OpenAI vs KURE v1 실제 문서 비교
- 품질 및 성능 종합 비교
- 실행: `python tests/archived/test_openai_vs_kure_real_document.py`

## GPU 성능 테스트

### `test_gpu_performance.py`
- GPU 환경에서의 성능 테스트
- GPU 메모리 사용량 및 처리 속도 측정
- 실행: `python tests/archived/test_gpu_performance.py`

### `test_gpu_vs_cpu_comparison.py`
- GPU vs CPU 성능 비교
- 처리량 및 효율성 비교
- 실행: `python tests/archived/test_gpu_vs_cpu_comparison.py`

## 문서 처리 테스트

### `test_complete_document_processing.py`
- 전체 문서 처리 워크플로우 테스트
- 청킹 + 임베딩 + 유사도 계산 통합 테스트
- 실행: `python tests/archived/test_complete_document_processing.py`

### `test_env_chunking.py`
- .env 설정을 사용한 전체 문서 청킹 테스트
- 환경 변수 기반 설정 테스트
- 실행: `python tests/archived/test_env_chunking.py`

### `test_env_chunking_partial.py`
- .env 설정을 사용한 부분 문서 청킹 테스트
- 실행: `python tests/archived/test_env_chunking_partial.py`

### `test_sample_chunking.py`
- 샘플 문서 청킹 테스트
- 다양한 청킹 전략 테스트
- 실행: `python tests/archived/test_sample_chunking.py`

## 기타 테스트

### `test_client.py`
- 간단한 테스트 클라이언트
- 기본적인 API 호출 테스트
- 실행: `python tests/archived/test_client.py`

### `test_new_defaults.py`
- 새로운 기본값 설정 테스트
- 기본 설정 변경 후 동작 확인
- 실행: `python tests/archived/test_new_defaults.py`

### `test_pdf_50_pages_simulation.py`
- 50페이지 PDF 문서 시뮬레이션 테스트
- 대용량 문서 처리 시뮬레이션
- 실행: `python tests/archived/test_pdf_50_pages_simulation.py`

## 사용법

이 테스트들을 실행하려면 메인 프로젝트 디렉토리에서 다음과 같이 실행하세요:

```bash
# 예시: 성능 비교 테스트
python tests/archived/test_performance_comparison.py

# 예시: GPU 성능 테스트
python tests/archived/test_gpu_performance.py
```

## 주의사항

- 일부 테스트는 특별한 환경 설정이 필요할 수 있습니다 (GPU, OpenAI API 키 등)
- 성능 테스트는 실행 시간이 오래 걸릴 수 있습니다
- 환경 변수 설정이 필요한 테스트들이 있습니다 (.env 파일 확인)
