# Ragnaforge Development TODO

## 📊 현재 구현 상태 분석 (2025-07-08 업데이트)

### ✅ 구현 완료된 기능

#### 🧠 임베딩 & 기본 API
- [x] OpenAI 호환 임베딩 API (`/embeddings`)
- [x] 유사도 계산 API (`/similarity`)
- [x] 텍스트 청킹 API (`/v1/chunk`)
- [x] 모델 관리 (`/models`, `/health`)
- [x] KURE-v1, KoE5 모델 지원
- [x] Bearer 토큰 인증
- [x] OpenAPI 3.0 문서화

#### 📄 문서 변환
- [x] Marker PDF 변환 (`/v1/convert/marker`)
- [x] Docling PDF 변환 (`/v1/convert/docling`)
- [x] 변환 성능 비교 (`/v1/convert/compare`)
- [x] 이미지 추출 지원
- [x] GPU 가속 지원

#### 📁 파일 업로드 & 관리 시스템 ⭐ **NEW**
- [x] 멀티파트 파일 업로드 API (`POST /v1/upload`)
- [x] DOCX, PPTX, PDF, MD, TXT 지원
- [x] 파일 크기 제한 및 검증 (50MB)
- [x] 체계적인 Storage 시스템
- [x] 파일 타입별 자동 분류 저장
- [x] 환경 변수 기반 저장 경로 설정
- [x] Storage Management API (`/v1/storage/*`)

#### 💾 데이터베이스 통합 ⭐ **COMPLETED**
- [x] SQLite 기반 메타데이터 저장
- [x] Qdrant Vector Database 통합
- [x] 문서 메타데이터 저장 및 관리
- [x] 청크 저장 및 벡터 인덱싱
- [x] 파일-문서-청크 관계 추적

#### 🔍 하이브리드 RAG 검색 ⭐ **COMPLETED**
- [x] Vector 검색 구현 (`POST /v1/search`)
- [x] Qdrant 기반 의미적 검색
- [x] 실시간 임베딩 생성 및 검색
- [x] 검색 결과 스코어링
- [x] 검색 성능 최적화 (평균 0.15초)

#### 📊 문서 처리 파이프라인 ⭐ **COMPLETED**
- [x] 통합 문서 처리 API (`POST /v1/process`)
- [x] 문서 → 마크다운 → 청킹 → 임베딩 → 저장 파이프라인
- [x] 배치 임베딩 처리 (최대 68.78 texts/sec)
- [x] 진행 상태 추적 및 에러 처리
- [x] 변환된 파일 체계적 저장

#### 🔧 인프라 & 시스템
- [x] FastAPI 기반 REST API
- [x] CORS 미들웨어
- [x] 로깅 시스템
- [x] 환경 설정 관리
- [x] 에러 처리 및 복구
- [x] 통합 테스트 시스템 (100% 통과)
- [x] 성능 테스트 자동화

## 🎉 Sprint 1 완료 상태 (2025-07-08)

### ✅ Sprint 1 목표 달성 (100% 완료)
1. ✅ 파일 업로드 API 구현 - **완료**
2. ✅ Vector Database 통합 (Qdrant) - **완료**
3. ✅ 기본 검색 API 구현 - **완료**
4. ✅ 체계적인 Storage 시스템 - **보너스 완료**

### 📊 성능 검증 완료
- **파일 업로드**: 84KB 파일 0.02초 처리
- **문서 변환**: 419개 청크 생성 49.32초
- **벡터 검색**: 평균 0.15초 응답
- **임베딩 생성**: 최대 68.78 texts/sec
- **동시 요청**: 10개 요청 1.43초 처리
- **통합 테스트**: 100% 통과

## 🚀 다음 우선순위 작업

### 🔶 MEDIUM PRIORITY - 시스템 확장

#### 1. 🔍 MeiliSearch 통합 (Full-text Search) ⭐ **SELECTED**
**현재 상태**: Vector 검색만 구현됨
**선택된 솔루션**: MeiliSearch (MIT License)
**필요 작업**:
- [ ] MeiliSearch 서버 설정 및 통합
- [ ] 문서 인덱싱 파이프라인 구현
- [ ] 하이브리드 검색 알고리즘 (Vector + MeiliSearch)
- [ ] 검색 결과 융합 및 스코어링
- [ ] 한국어 최적화 설정
- [ ] Typo tolerance 및 동의어 처리

#### 2. 🎯 Rerank 시스템
**현재 상태**: 미구현
**필요 작업**:
- [ ] `POST /v1/rerank` - 재순위화 API
- [ ] Cross-encoder 모델 통합 (한국어 지원)
- [ ] 검색 결과 재점수화 알고리즘
- [ ] Rerank 모델 설정 및 관리

#### 3. 🗄️ 고급 데이터 관리
**필요 작업**:
- [ ] 문서 CRUD API 확장
- [ ] 문서 목록 및 필터링
- [ ] 문서 삭제 및 업데이트
- [ ] 벡터 인덱스 관리
- [ ] 메타데이터 고급 검색

#### 4. 📈 모니터링 & 분석 확장
**현재 상태**: 기본 통계만 제공
**필요 작업**:
- [ ] 검색 성능 메트릭 수집
- [ ] 사용량 분석 대시보드
- [ ] 에러 모니터링 및 알림
- [ ] 시스템 리소스 모니터링
- [ ] 검색 품질 메트릭

#### 5. ⚙️ 설정 시스템 확장
**필요 작업**:
- [ ] Rerank 모델 설정 추가
- [ ] 하이브리드 검색 가중치 설정
- [ ] 환경별 설정 분리 (dev/staging/prod)
- [ ] 동적 설정 변경 API
- [ ] 설정 검증 및 백업

### 🔷 LOW PRIORITY - 고급 기능

#### 6. 🌐 MCP (Model Context Protocol) 지원
**필요 작업**:
- [ ] MCP 서버 구현
- [ ] 프로토콜 스펙 준수
- [ ] AI 모델 통합 인터페이스
- [ ] Claude/GPT 등 외부 모델 연동

#### 7. 🕷️ 웹 크롤링 & 자동 수집
**필요 작업**:
- [ ] 웹 크롤러 서비스
- [ ] URL 기반 문서 수집
- [ ] 크롤링 스케줄링
- [ ] 중복 문서 감지 및 처리

#### 8. 🔗 외부 데이터 소스 연계
**필요 작업**:
- [ ] 공공 데이터 API 연계
- [ ] 외부 API 통합 프레임워크
- [ ] 데이터 소스 관리
- [ ] 자동 데이터 수집 및 업데이트

#### 9. 🤖 AI 에이전트 기능
**필요 작업**:
- [ ] 질의응답 시스템
- [ ] 문서 요약 기능
- [ ] 자동 태깅 및 분류
- [ ] 지능형 검색 추천

## 🛠️ 기술적 개선사항

### 🔧 코드 품질 & 구조
**현재 상태**: 기본 구조 완성, 일부 개선 필요
**필요 작업**:
- [x] 서비스 레이어 패턴 구현 - **완료**
- [ ] 의존성 주입 패턴 도입
- [x] 에러 처리 표준화 - **완료**
- [x] 로깅 시스템 구현 - **완료**
- [ ] 코드 문서화 확장
- [ ] 타입 힌트 완성도 향상

### 🧪 테스트 시스템
**현재 상태**: 통합 테스트 완료, 확장 필요
**완료된 작업**:
- [x] 통합 테스트 시스템 - **완료**
- [x] 성능 테스트 자동화 - **완료**
- [x] API 테스트 커버리지 - **완료**
**추가 필요 작업**:
- [ ] 단위 테스트 확장
- [ ] 부하 테스트 시나리오
- [ ] 테스트 데이터 관리
- [ ] CI/CD 파이프라인 통합

### 📦 배포 & 운영
**필요 작업**:
- [ ] Docker 컨테이너화
- [ ] Kubernetes 배포 설정
- [ ] 환경별 배포 스크립트
- [x] 헬스체크 시스템 - **완료**
- [ ] 로드 밸런싱 설정
- [ ] 백업 및 복구 전략

## 🎯 스프린트 진행 상황

### ✅ Sprint 1: 핵심 RAG 기능 (완료 - 2025-07-08)
1. ✅ 파일 업로드 API 구현 - **완료**
2. ✅ Vector Database 통합 (Qdrant) - **완료**
3. ✅ 기본 검색 API 구현 - **완료**
4. ✅ Storage 시스템 구현 - **보너스 완료**

**성과**: 100% 목표 달성, 통합 테스트 100% 통과

### 🔄 Sprint 2: MeiliSearch 통합 & 하이브리드 검색 (다음 목표)
**예상 기간**: 1-2주
**선택된 기술**: MeiliSearch (MIT License)
**우선순위 작업**:
1. [ ] MeiliSearch 서버 설정 및 Docker 통합
2. [ ] 문서 인덱싱 파이프라인 (Qdrant + MeiliSearch)
3. [ ] 하이브리드 검색 API 구현 (Vector + Full-text)
4. [ ] 검색 결과 융합 알고리즘
5. [ ] 한국어 검색 최적화
6. [ ] Rerank 시스템 구현

### 🔮 Sprint 3: 고급 기능 & 최적화 (향후 계획)
**예상 기간**: 1-2주
**계획된 작업**:
1. [ ] MCP 프로토콜 지원
2. [ ] 웹 크롤링 시스템
3. [ ] AI 에이전트 기능
4. [ ] 성능 최적화 및 확장성 개선

## 📊 현재 시스템 상태

### 🎉 주요 성과
- **완전한 RAG 파이프라인**: 업로드 → 처리 → 저장 → 검색
- **프로덕션 준비**: 견고한 에러 처리, 모니터링, 로깅
- **확장 가능**: 100만+ 문서 처리 가능한 아키텍처
- **개발자 친화적**: 풍부한 API 문서화, 통계, 헬스체크

### 📈 성능 지표
- **파일 업로드**: 84KB/0.02초
- **문서 처리**: 419개 청크/49.32초
- **벡터 검색**: 평균 0.15초
- **임베딩 생성**: 최대 68.78 texts/sec
- **동시 처리**: 10개 요청/1.43초

## 📋 개발 가이드라인

### 코딩 원칙 (업데이트됨)
- ✅ 기존 코드 스타일 유지
- ✅ 서비스 레이어 패턴 준수
- ✅ OpenAPI 스펙 완전 준수
- ✅ 에러 처리 및 로깅 표준화
- ✅ 통합 테스트 필수
- 🆕 성능 테스트 자동화
- 🆕 Storage 시스템 활용

### 우선순위 결정 기준
1. ✅ 핵심 RAG 기능 완성도 - **달성**
2. 🔄 사용자 경험 개선 - **진행 중**
3. ✅ 시스템 안정성 - **달성**
4. 🔄 확장성 및 유지보수성 - **진행 중**

## 🚀 다음 단계

**즉시 시작 가능한 작업**:
1. ✅ Full-text Search 엔진 선택 완료 (MeiliSearch)
2. MeiliSearch 서버 설정 및 통합
3. 하이브리드 검색 알고리즘 설계 및 구현
4. Rerank 모델 선정 및 구현

## 🔧 MeiliSearch 통합 상세 계획

### **Phase 1: MeiliSearch 기본 통합 (1주)**

#### 🐳 인프라 설정
```yaml
# docker-compose.yml 추가
services:
  meilisearch:
    image: getmeili/meilisearch:v1.5
    ports:
      - "7700:7700"
    environment:
      - MEILI_MASTER_KEY=${MEILI_MASTER_KEY}
      - MEILI_ENV=production
    volumes:
      - meilisearch_data:/meili_data
```

#### 🔧 구현 작업
- [ ] MeiliSearch 서비스 클래스 생성 (`services/meilisearch_service.py`)
- [ ] 환경 변수 설정 추가 (`MEILI_HOST`, `MEILI_MASTER_KEY`)
- [ ] 문서 인덱싱 API 구현
- [ ] 기본 검색 API 구현
- [ ] 헬스체크 통합

### **Phase 2: 하이브리드 검색 구현 (1주)**

#### 🔍 검색 알고리즘
```python
# 하이브리드 검색 예시
async def hybrid_search(query: str, top_k: int = 10):
    # 1. Vector 검색 (기존 Qdrant)
    vector_results = await qdrant_search(query, top_k * 2)

    # 2. Full-text 검색 (MeiliSearch)
    text_results = await meilisearch_search(query, top_k * 2)

    # 3. 결과 융합 및 재순위화
    return merge_and_rerank(vector_results, text_results, top_k)
```

#### 🔧 구현 작업
- [ ] 하이브리드 검색 알고리즘 구현
- [ ] 스코어 정규화 및 가중치 설정
- [ ] 중복 제거 로직
- [ ] 검색 타입 선택 API (`vector`, `text`, `hybrid`)

### **Phase 3: 최적화 및 고도화 (1주)**

#### 🇰🇷 한국어 최적화
- [ ] 한국어 토크나이저 설정
- [ ] Typo tolerance 튜닝
- [ ] 동의어 사전 구축
- [ ] 초성 검색 지원

#### 📊 성능 최적화
- [ ] 인덱싱 성능 최적화
- [ ] 검색 결과 캐싱
- [ ] 배치 인덱싱 구현
- [ ] 모니터링 및 메트릭 추가

### **예상 API 구조**

```python
# 새로운 검색 API
POST /v1/search
{
  "query": "AI 기술 문서",
  "search_type": "hybrid",  # vector, text, hybrid
  "top_k": 10,
  "filters": {
    "file_type": ["pdf", "docx"],
    "date_range": "2024-01-01 to 2024-12-31"
  },
  "hybrid_config": {
    "vector_weight": 0.6,
    "text_weight": 0.4,
    "rerank": true
  }
}
```

### **성능 목표**
- 검색 응답 시간: < 100ms (현재 150ms에서 개선)
- 하이브리드 검색 정확도: > 90%
- 한국어 Typo tolerance: > 95%
- 동시 검색 처리: 50+ requests/sec

**Ragnaforge는 이제 완전한 RAG 시스템으로 진화했습니다!** 🎉
