#!/usr/bin/env python3
"""
Ragnaforge 테스트 실행 스크립트

이 스크립트는 Ragnaforge의 모든 테스트를 실행하고 결과를 요약합니다.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description):
    """명령어를 실행하고 결과를 반환합니다."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        execution_time = time.time() - start_time
        
        print(f"⏱️  실행 시간: {execution_time:.2f}초")
        
        if result.returncode == 0:
            print("✅ 성공!")
            if result.stdout:
                print("\n📋 출력:")
                print(result.stdout)
        else:
            print("❌ 실패!")
            if result.stderr:
                print("\n🚨 오류:")
                print(result.stderr)
            if result.stdout:
                print("\n📋 출력:")
                print(result.stdout)
        
        return result.returncode == 0, execution_time
        
    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {str(e)}")
        return False, 0


def main():
    """메인 테스트 실행 함수"""
    print("🚀 Ragnaforge 테스트 스위트 실행")
    print(f"📁 작업 디렉토리: {Path.cwd()}")
    
    total_start_time = time.time()
    results = []
    
    # 1. 환경 확인
    success, exec_time = run_command(
        "python -c \"import sys; print(f'Python: {sys.version}'); import pytest; print(f'pytest: {pytest.__version__}')\"",
        "환경 확인"
    )
    results.append(("환경 확인", success, exec_time))
    
    # 2. 의존성 확인
    success, exec_time = run_command(
        "python -c \"from services.embedding_service import embedding_service; from services.qdrant_service import qdrant_service; print('✅ 모든 서비스 임포트 성공')\"",
        "서비스 의존성 확인"
    )
    results.append(("서비스 의존성", success, exec_time))
    
    # 3. 통합 테스트 실행
    success, exec_time = run_command(
        "python -m pytest tests/test_integration_simple.py -v -s --tb=short",
        "통합 테스트 실행"
    )
    results.append(("통합 테스트", success, exec_time))

    # 4. Rerank 서비스 테스트 실행
    success, exec_time = run_command(
        "python -m pytest tests/test_rerank_service.py -v -s --tb=short",
        "Rerank 서비스 테스트 실행"
    )
    results.append(("Rerank 테스트", success, exec_time))

    # 5. Search + Rerank 통합 테스트 실행
    success, exec_time = run_command(
        "python -m pytest tests/test_search_with_rerank.py -v -s --tb=short",
        "Search + Rerank 통합 테스트 실행"
    )
    results.append(("통합 테스트", success, exec_time))

    # 6. 전체 테스트 실행 (다른 테스트 파일이 있는 경우)
    success, exec_time = run_command(
        "python -m pytest tests/ -v --tb=short",
        "전체 테스트 실행"
    )
    results.append(("전체 테스트", success, exec_time))
    
    # 7. 서비스 헬스 체크
    success, exec_time = run_command(
        "python -c \"from services.qdrant_service import qdrant_service; from services.rerank_service import rerank_service; from services.unified_search_service import unified_search_service; health = qdrant_service.health_check(); print(f'Qdrant: {health}'); print(f'Rerank enabled: {rerank_service.is_enabled()}'); print(f'Unified Search: {unified_search_service.is_initialized}')\"",
        "서비스 헬스 체크"
    )
    results.append(("헬스 체크", success, exec_time))
    
    # 결과 요약
    total_time = time.time() - total_start_time
    
    print(f"\n{'='*60}")
    print("📊 테스트 결과 요약")
    print(f"{'='*60}")
    
    success_count = 0
    for test_name, success, exec_time in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{test_name:20} | {status:8} | {exec_time:6.2f}초")
        if success:
            success_count += 1
    
    print(f"\n🎯 총 {len(results)}개 테스트 중 {success_count}개 성공")
    print(f"⏱️  총 실행 시간: {total_time:.2f}초")
    
    if success_count == len(results):
        print("\n🎉 모든 테스트가 성공했습니다!")
        return 0
    else:
        print(f"\n⚠️  {len(results) - success_count}개 테스트가 실패했습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
