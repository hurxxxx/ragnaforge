# 🚀 KURE v1 GPU 성능 테스트 가이드

GPU 서버에서 KURE v1 API Gateway의 성능을 테스트하는 간단한 가이드입니다.

## 📋 사전 준비

### 필수 요구사항
- **GPU 서버** (NVIDIA GPU + CUDA 지원)
- **Python 3.8+**
- **Git**
- **Conda** 또는 **Python venv**

### GPU 확인
```bash
# GPU 상태 확인
nvidia-smi

# CUDA 버전 확인
nvcc --version
```

## 🔧 1단계: 환경 설정 (최초 1회)

### 저장소 클론
```bash
git clone <your-repo-url>
cd kure-v1-api-gateway
```

### 자동 환경 설정
```bash
# 실행 권한 부여
chmod +x setup_gpu_server.sh

# GPU 환경 자동 설정 (5-10분 소요)
./setup_gpu_server.sh
```

**설정 완료 시 다음이 자동으로 설치됩니다:**
- ✅ Conda 환경 (ragnaforge)
- ✅ PyTorch with CUDA
- ✅ 필요한 Python 패키지들
- ✅ GPU 최적화 설정

## 🚀 2단계: 서버 시작

### 환경 활성화
```bash
# Conda 사용 시
conda activate ragnaforge

# 또는 venv 사용 시
source venv/bin/activate
```

### 서버 실행
```bash
# 백그라운드 실행
python main.py &

# 또는 포그라운드 실행
python main.py
```

### 서버 상태 확인
```bash
# 헬스 체크
curl http://localhost:8000/health

# 응답 예시: {"status":"healthy","is_model_loaded":true,"version":"1.0.0"}
```

## 🧪 3단계: 성능 테스트 실행

### 원클릭 테스트 (권장)
```bash
# 종합 성능 테스트 실행
./run_gpu_test.sh
```

### 개별 테스트
```bash
# GPU 성능 테스트
python tests/test_gpu_performance.py

# GPU vs CPU 비교
python tests/test_gpu_vs_cpu_comparison.py

# 배치 크기 최적화
python tests/test_batch_size_optimization.py
```

## 📊 4단계: 결과 분석

### 예상 테스트 결과

#### **GPU 성능 향상 (CPU 대비)**
| GPU 모델 | 예상 향상 | 50페이지 문서 처리 시간 |
|----------|-----------|------------------------|
| RTX 3060 | 5-8배 | 9-14초 |
| RTX 3080 | 8-12배 | 6-9초 |
| RTX 4090 | 15-25배 | 4-7초 |
| A100 | 20-30배 | 3-5초 |

#### **OpenAI 대비 성능**
| 항목 | KURE v1 (GPU) | OpenAI Large | 우위 |
|------|---------------|--------------|------|
| **속도** | 5-7초 | 7.2초 | 🥇 더 빠름 |
| **품질** | 0.4435 | 0.3540 | 🥇 25% 더 정확 |
| **비용** | 무료 | $0.0044 | 🥇 완전 무료 |

### 최적 배치 크기 확인
테스트 결과에서 **가장 높은 chunks/second**를 보이는 배치 크기를 확인하세요.

```
예시 결과:
Batch Size 16: 45.2 chunks/second ← 최적
Batch Size 32: 52.1 chunks/second ← 더 좋음
Batch Size 64: 48.3 chunks/second
```

## ⚙️ 5단계: 설정 최적화

### .env 파일 수정
```bash
# 테스트 결과에 따라 최적 배치 크기 설정
nano .env

# 예시: RTX 3080의 경우
MAX_BATCH_SIZE=64
OPTIMAL_BATCH_SIZE=64
```

### GPU별 권장 설정
```bash
# 8GB GPU (RTX 3060Ti, RTX 2080)
MAX_BATCH_SIZE=32

# 12-16GB GPU (RTX 3080, RTX 4070)
MAX_BATCH_SIZE=64

# 24GB+ GPU (RTX 4090, A100)
MAX_BATCH_SIZE=128
```

## 📈 6단계: 모니터링

### 실시간 GPU 모니터링
```bash
# GPU 사용량 실시간 모니터링
./monitor_gpu.sh

# 또는 기본 명령어
watch -n 1 nvidia-smi
```

### 성능 로그 확인
```bash
# API 로그 확인
tail -f logs/api.log

# 시스템 리소스 확인
htop
```

## 🎯 빠른 성능 확인

### 간단한 성능 테스트
```bash
# 50개 텍스트로 빠른 테스트
curl -X POST "http://localhost:8000/embeddings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-kure-v1-test-key-12345" \
  -d '{
    "input": ["테스트 문장 1", "테스트 문장 2", "테스트 문장 3"],
    "model": "nlpai-lab/KURE-v1"
  }'
```

### 처리 시간 측정
```bash
# 시간 측정과 함께 테스트
time python tests/test_gpu_performance.py
```

## 🔧 문제 해결

### 일반적인 문제들

#### GPU 메모리 부족
```bash
# 배치 크기 줄이기
MAX_BATCH_SIZE=16

# GPU 메모리 정리
python -c "import torch; torch.cuda.empty_cache()"
```

#### CUDA 오류
```bash
# PyTorch CUDA 재설치
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### 서버 연결 실패
```bash
# 포트 확인
netstat -tlnp | grep 8000

# 방화벽 확인
sudo ufw status
```

## 📊 성능 비교 요약

### CPU vs GPU 예상 결과
```
CPU (현재):     112초 (50페이지 문서)
GPU (예상):     7-22초 (5-15배 향상)
OpenAI Large:   7.2초
```

### 비즈니스 가치
- **속도**: OpenAI와 동등하거나 더 빠름
- **품질**: 25% 더 정확한 한국어 처리
- **비용**: 완전 무료 (API 비용 없음)
- **보안**: 로컬 처리 (데이터 외부 유출 없음)

## 🎉 테스트 완료 후

### 결과 공유
테스트 결과를 다음 형식으로 정리해주세요:

```
GPU 모델: RTX 3080
배치 크기: 64
50페이지 문서 처리 시간: 8.5초
CPU 대비 향상: 13.2배
OpenAI 대비: 1.2배 빠름
```

### 프로덕션 배포
성능이 만족스럽다면 프로덕션 환경에 배포하세요:

```bash
# 프로덕션 설정
cp .env.gpu .env.production

# 서비스 등록
sudo systemctl enable ragnaforge
sudo systemctl start ragnaforge
```

---

**🚀 Happy Testing!**

문제가 있거나 추가 도움이 필요하시면 언제든 문의해주세요!
