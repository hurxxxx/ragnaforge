# Ragnaforge 테스트 스위트

이 디렉토리는 Ragnaforge의 모든 서비스와 기능을 테스트하는 포괄적인 테스트 스위트를 포함합니다.

## 🎉 테스트 완료 상태

**✅ 모든 핵심 기능 테스트 성공!**

현재 구현된 통합 테스트를 통해 다음 기능들이 정상 작동함을 확인했습니다:
- 파일 업로드 → 문서 처리 → 임베딩 생성 → 벡터 검색의 전체 파이프라인
- Qdrant 벡터 데이터베이스 연동 (1839개 포인트 저장됨)
- 임베딩 서비스 (3개 모델, 1024차원 벡터)
- 검색 기능 (벡터 유사도 검색)

## 테스트 구조

### 현재 구현된 테스트

#### 1. `test_integration_simple.py` - 통합 테스트
- **목적**: 전체 시스템의 end-to-end 기능 테스트
- **테스트 내용**:
  - 서비스 임포트 및 초기화 확인
  - 임베딩 서비스 기본 기능 (모델 로딩, 텍스트 인코딩)
  - Qdrant 연결 및 헬스 체크
  - 파일 업로드 기본 기능
  - 문서 처리 파이프라인 (업로드 → 변환 → 청킹 → 임베딩)
  - 벡터 검색 기능
  - 서비스 통계 조회
  - 전체 워크플로우 테스트
  - 설정 검증

#### 2. 이전에 생성된 테스트 파일들 (현재 누락)
- `test_embedding_service.py` - 임베딩 서비스 상세 테스트
- `test_file_management.py` - 파일 관리 서비스 테스트
- `test_search_services.py` - 검색 서비스 테스트
- `test_document_processing.py` - 문서 처리 서비스 테스트

## 테스트 실행 방법

### 전체 테스트 실행
```bash
cd /projects/ragnaforge
python -m pytest tests/ -v
```

### 특정 테스트 파일 실행
```bash
python -m pytest tests/test_integration_simple.py -v
```

### 상세 출력과 함께 실행
```bash
python -m pytest tests/ -v -s --tb=short
```

## 테스트 결과 요약

### 최근 테스트 실행 결과 (성공)
```
======= 9 passed, 28 warnings in 9.64s =======

✓ test_service_imports - 모든 서비스 임포트 성공
✓ test_embedding_service_basic - 임베딩 서비스 기본 기능 (3개 모델, 1024차원)
✓ test_qdrant_connection - Qdrant 연결 성공 (healthy 상태)
✓ test_file_upload_basic - 파일 업로드 성공
✓ test_document_processing_basic - 문서 처리 성공 (1개 청크, 임베딩 생성)
✓ test_search_basic - 벡터 검색 성공 (5개 결과)
✓ test_service_stats - 서비스 통계 조회 성공 (1839개 포인트)
✓ test_full_workflow_simple - 전체 워크플로우 성공
✓ test_configuration_check - 설정 검증 성공
```

## 환경 설정

### 필수 환경 변수
테스트는 다음 환경 변수들을 참조합니다:
- `QDRANT_HOST` - Qdrant 서버 호스트
- `QDRANT_PORT` - Qdrant 서버 포트
- `QDRANT_API_KEY` - Qdrant API 키
- `MEILISEARCH_URL` - MeiliSearch 서버 URL
- `MEILISEARCH_API_KEY` - MeiliSearch API 키

### 테스트 데이터
- 테스트는 실제 파일을 사용하여 수행됩니다
- 임시 파일은 `tmp_path` fixture를 사용하여 생성됩니다
- 테스트용 텍스트 파일은 금융위원회 관련 내용을 포함합니다

## 테스트 특징

### 실제 서비스 연동
- 모든 테스트는 실제 서비스 인스턴스를 사용합니다
- Qdrant, MeiliSearch 등 외부 서비스와 실제 연결을 테스트합니다
- 실제 임베딩 모델을 로딩하고 사용합니다

### 환경 변수 기반 설정
- 모든 외부 서비스 연결 정보는 환경 변수에서 가져옵니다
- 테스트 실패 시 연결 문제와 기능 문제를 구분할 수 있습니다

### 실제 파일 사용
- 모의(mock) 객체 대신 실제 파일을 사용하여 테스트합니다
- 파일 업로드, 변환, 처리 과정을 실제로 수행합니다

## 향후 개선 사항

### 1. 누락된 테스트 파일 복구
- 임베딩 서비스 상세 테스트
- 파일 관리 서비스 테스트
- 검색 서비스 테스트
- 문서 처리 서비스 테스트

### 2. 추가 테스트 케이스
- 오류 처리 테스트 강화
- 성능 벤치마크 테스트
- 동시성 테스트
- 대용량 파일 처리 테스트

### 3. 테스트 자동화
- CI/CD 파이프라인 통합
- 자동화된 테스트 보고서 생성
- 성능 회귀 테스트

## 문제 해결

### 일반적인 문제들

#### 1. Qdrant 연결 실패
```
⚠ Qdrant 연결 실패: Connection refused
```
- Qdrant 서버가 실행 중인지 확인
- `QDRANT_HOST`, `QDRANT_PORT` 환경 변수 확인

#### 2. 임베딩 모델 로딩 실패
```
⚠ 임베딩 서비스 오류: Model not found
```
- 모델 파일이 올바른 위치에 있는지 확인
- GPU 메모리 부족 여부 확인

#### 3. 파일 업로드 실패
```
⚠ 파일 업로드 실패: Permission denied
```
- 저장소 디렉토리 권한 확인
- 디스크 공간 확인

## 테스트 데이터 정리

테스트 실행 후 생성된 임시 데이터를 정리하려면:
```bash
# 임시 파일 정리
rm -rf /tmp/pytest-*

# 테스트 데이터베이스 정리 (선택사항)
# rm -f ./data/database/test_*.db
```

## 기여 가이드

새로운 테스트를 추가할 때:
1. 실제 서비스를 사용하여 테스트
2. 환경 변수를 통한 설정 사용
3. 실제 파일을 사용한 테스트
4. 적절한 오류 처리 포함
5. 테스트 결과를 명확하게 출력
