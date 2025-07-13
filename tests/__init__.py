"""
Ragnaforge 테스트 패키지

이 패키지는 Ragnaforge의 모든 서비스와 기능을 테스트하는 포괄적인 테스트 스위트를 제공합니다.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 테스트용 환경 변수 설정
os.environ.setdefault("TESTING", "true")
