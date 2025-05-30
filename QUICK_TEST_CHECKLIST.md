# ⚡ KURE v1 GPU 테스트 빠른 체크리스트

GPU 서버에서 5분 만에 성능 테스트하는 체크리스트입니다.

## 🔥 초고속 테스트 (5분)

### ✅ 1. 환경 확인 (30초)
```bash
nvidia-smi                    # GPU 확인
python3 --version            # Python 확인
```

### ✅ 2. 프로젝트 설정 (2분)
```bash
git clone <repo-url>
cd kure-v1-api-gateway
./setup_gpu_server.sh        # 자동 설정
```

### ✅ 3. 서버 시작 (30초)
```bash
conda activate kure-api
python main.py &             # 백그라운드 실행
curl http://localhost:8000/health  # 상태 확인
```

### ✅ 4. 성능 테스트 (2분)
```bash
./run_gpu_test.sh            # 원클릭 테스트
```

---

## 🎯 핵심 명령어 모음

### 환경 설정
```bash
./setup_gpu_server.sh        # 전체 환경 설정
conda activate kure-api       # 환경 활성화
```

### 서버 관리
```bash
python main.py               # 서버 시작
curl localhost:8000/health   # 상태 확인
pkill -f "python main.py"    # 서버 종료
```

### 성능 테스트
```bash
./run_gpu_test.sh                           # 종합 테스트
python tests/test_gpu_performance.py        # GPU 성능
python tests/test_gpu_vs_cpu_comparison.py  # GPU vs CPU
```

### 모니터링
```bash
./monitor_gpu.sh             # GPU 모니터링
nvidia-smi                   # GPU 상태
htop                         # 시스템 리소스
```

---

## 📊 예상 결과 (참고용)

### GPU별 성능 향상
- **RTX 3060**: 5-8배 → 9-14초
- **RTX 3080**: 8-12배 → 6-9초  
- **RTX 4090**: 15-25배 → 4-7초

### OpenAI 대비
- **속도**: 동등하거나 더 빠름
- **품질**: 25% 더 정확
- **비용**: 완전 무료

---

## 🔧 문제 해결

### GPU 메모리 부족
```bash
# .env 파일에서 배치 크기 줄이기
MAX_BATCH_SIZE=16
```

### CUDA 오류
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### 서버 연결 실패
```bash
netstat -tlnp | grep 8000    # 포트 확인
```

---

## ✅ 성공 기준

### 테스트 성공 지표
- [ ] GPU 인식됨 (`nvidia-smi` 정상)
- [ ] 서버 시작됨 (`/health` 응답 OK)
- [ ] 배치 처리 성공 (에러 없음)
- [ ] CPU 대비 5배+ 향상
- [ ] OpenAI 대비 동등한 속도

### 최적화 완료 지표
- [ ] 최적 배치 크기 확인
- [ ] GPU 메모리 80% 이하 사용
- [ ] 안정적인 처리 속도
- [ ] 에러율 0%

---

**🚀 5분 만에 GPU 성능 확인 완료!**
