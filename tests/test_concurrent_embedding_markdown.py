#!/usr/bin/env python3
"""
동시 처리 능력 테스트: Embedding + Markdown 변환(Marker) 세트 실행
workers=1 환경에서 동시 실행 수를 증가시켜 성능 체크
"""

import asyncio
import aiohttp
import time
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import statistics
import psutil

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConcurrentTestConfig:
    """동시 처리 테스트 설정"""
    base_url: str = "http://localhost:8000"
    api_key: str = ""  # 인증 비활성화
    concurrent_levels: List[int] = None
    test_duration: int = 30  # 각 레벨당 테스트 시간(초)
    sample_texts: List[str] = None
    sample_pdf_path: str = "sample_docs/sample2.pdf"
    
    def __post_init__(self):
        if self.concurrent_levels is None:
            self.concurrent_levels = [1, 2, 4, 8, 16]
        
        if self.sample_texts is None:
            self.sample_texts = [
                "한국어 임베딩 모델 KURE v1의 성능을 테스트합니다.",
                "자연어 처리 기술의 발전으로 다양한 응용이 가능해졌습니다.",
                "문서 변환과 임베딩을 동시에 처리하는 성능을 측정합니다.",
                "동시 처리 능력은 실제 서비스에서 중요한 지표입니다.",
                "PDF 문서를 마크다운으로 변환하고 임베딩을 생성합니다."
            ]

@dataclass
class RequestResult:
    """개별 요청 결과"""
    request_type: str  # "embedding" or "markdown"
    success: bool
    response_time: float
    error_message: Optional[str] = None
    response_size: int = 0

@dataclass
class ConcurrentTestResult:
    """동시 처리 테스트 결과"""
    concurrent_level: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    avg_response_time: float
    requests_per_second: float
    embedding_results: List[RequestResult]
    markdown_results: List[RequestResult]
    system_metrics: Dict[str, Any]

class SystemMonitor:
    """시스템 리소스 모니터링"""
    
    def __init__(self):
        self.metrics = []
        self.monitoring = False
    
    async def start_monitoring(self, interval: float = 1.0):
        """모니터링 시작"""
        self.monitoring = True
        self.metrics = []
        
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                
                metric = {
                    "timestamp": time.time(),
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "memory_available_gb": memory.available / (1024**3)
                }
                
                self.metrics.append(metric)
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"모니터링 오류: {e}")
                break
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring = False
    
    def get_summary(self) -> Dict[str, Any]:
        """모니터링 결과 요약"""
        if not self.metrics:
            return {}
        
        cpu_values = [m["cpu_percent"] for m in self.metrics]
        memory_values = [m["memory_percent"] for m in self.metrics]
        
        return {
            "avg_cpu_percent": statistics.mean(cpu_values),
            "max_cpu_percent": max(cpu_values),
            "avg_memory_percent": statistics.mean(memory_values),
            "max_memory_percent": max(memory_values),
            "max_memory_used_gb": max(m["memory_used_gb"] for m in self.metrics),
            "sample_count": len(self.metrics)
        }

class ConcurrentTester:
    """동시 처리 테스트 실행기"""
    
    def __init__(self, config: ConcurrentTestConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.monitor = SystemMonitor()
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        headers = {
            "Content-Type": "application/json"
        }

        # API 키가 있는 경우에만 Authorization 헤더 추가
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    async def make_embedding_request(self, texts: List[str]) -> RequestResult:
        """임베딩 요청"""
        start_time = time.time()
        
        try:
            payload = {
                "input": texts,
                "model": "nlpai-lab/KURE-v1"
            }
            
            async with self.session.post(
                f"{self.config.base_url}/embeddings",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    return RequestResult(
                        request_type="embedding",
                        success=True,
                        response_time=response_time,
                        response_size=len(str(data))
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"Embedding 요청 실패: HTTP {response.status}: {error_text}")
                    return RequestResult(
                        request_type="embedding",
                        success=False,
                        response_time=response_time,
                        error_message=f"HTTP {response.status}: {error_text}"
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Embedding 요청 예외: {e}")
            return RequestResult(
                request_type="embedding",
                success=False,
                response_time=response_time,
                error_message=str(e)
            )
    
    async def make_markdown_request(self, pdf_path: str) -> RequestResult:
        """마크다운 변환 요청 (Marker만 사용)"""
        start_time = time.time()
        
        try:
            payload = {
                "file_path": pdf_path,
                "extract_images": False
            }
            
            async with self.session.post(
                f"{self.config.base_url}/v1/convert/marker",
                json=payload
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    return RequestResult(
                        request_type="markdown",
                        success=True,
                        response_time=response_time,
                        response_size=len(str(data))
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"Markdown 요청 실패: HTTP {response.status}: {error_text}")
                    return RequestResult(
                        request_type="markdown",
                        success=False,
                        response_time=response_time,
                        error_message=f"HTTP {response.status}: {error_text}"
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Markdown 요청 예외: {e}")
            return RequestResult(
                request_type="markdown",
                success=False,
                response_time=response_time,
                error_message=str(e)
            )
    
    async def run_concurrent_set(self, concurrent_level: int) -> ConcurrentTestResult:
        """동시 처리 세트 실행 (embedding + markdown 쌍으로)"""
        logger.info(f"🚀 동시 처리 테스트 시작: {concurrent_level}개 세트")

        # 시스템 모니터링 시작
        monitor_task = asyncio.create_task(self.monitor.start_monitoring(interval=0.5))

        embedding_results = []
        markdown_results = []
        start_time = time.time()

        # 고정된 수의 세트를 실행 (시간 기반이 아닌 횟수 기반)
        total_sets = concurrent_level * 3  # 각 레벨당 3배수만큼 세트 실행

        async def run_single_set():
            """단일 세트 실행 (embedding + markdown)"""
            # 임베딩과 마크다운 변환을 동시에 실행
            embedding_task = self.make_embedding_request(self.config.sample_texts[:2])
            markdown_task = self.make_markdown_request(self.config.sample_pdf_path)

            embedding_result, markdown_result = await asyncio.gather(
                embedding_task, markdown_task, return_exceptions=True
            )

            # 예외 처리
            if isinstance(embedding_result, Exception):
                embedding_result = RequestResult(
                    request_type="embedding",
                    success=False,
                    response_time=0,
                    error_message=str(embedding_result)
                )

            if isinstance(markdown_result, Exception):
                markdown_result = RequestResult(
                    request_type="markdown",
                    success=False,
                    response_time=0,
                    error_message=str(markdown_result)
                )

            return embedding_result, markdown_result

        # 세마포어로 동시 실행 수 제한
        semaphore = asyncio.Semaphore(concurrent_level)

        async def run_limited_set():
            """세마포어로 제한된 세트 실행"""
            async with semaphore:
                return await run_single_set()

        # 모든 세트를 동시에 시작하되, 세마포어로 동시 실행 수 제한
        tasks = [asyncio.create_task(run_limited_set()) for _ in range(total_sets)]

        # 모든 태스크 완료 대기
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 분리
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"세트 실행 오류: {result}")
                # 실패한 세트는 실패 결과로 추가
                embedding_results.append(RequestResult(
                    request_type="embedding", success=False, response_time=0, error_message=str(result)
                ))
                markdown_results.append(RequestResult(
                    request_type="markdown", success=False, response_time=0, error_message=str(result)
                ))
            elif isinstance(result, tuple) and len(result) == 2:
                emb_result, md_result = result
                embedding_results.append(emb_result)
                markdown_results.append(md_result)
            else:
                logger.error(f"예상치 못한 결과 형식: {result}")
                # 예상치 못한 결과도 실패로 처리
                embedding_results.append(RequestResult(
                    request_type="embedding", success=False, response_time=0, error_message="Unexpected result format"
                ))
                markdown_results.append(RequestResult(
                    request_type="markdown", success=False, response_time=0, error_message="Unexpected result format"
                ))

        total_time = time.time() - start_time

        # 모니터링 중지
        self.monitor.stop_monitoring()
        monitor_task.cancel()

        # 결과 계산
        total_requests = len(embedding_results) + len(markdown_results)
        successful_requests = sum(1 for r in embedding_results + markdown_results if r.success)
        failed_requests = total_requests - successful_requests

        all_response_times = [r.response_time for r in embedding_results + markdown_results if r.success]
        avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
        requests_per_second = total_requests / total_time if total_time > 0 else 0

        return ConcurrentTestResult(
            concurrent_level=concurrent_level,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time=total_time,
            avg_response_time=avg_response_time,
            requests_per_second=requests_per_second,
            embedding_results=embedding_results,
            markdown_results=markdown_results,
            system_metrics=self.monitor.get_summary()
        )

async def main():
    """메인 테스트 실행"""
    print("🧪 동시 처리 능력 테스트: Embedding + Markdown 변환 세트")
    print("=" * 60)
    
    # 설정
    config = ConcurrentTestConfig(
        concurrent_levels=[ 2, 4, 6, 8],  # 동시 실행 세트 수
        test_duration=10  # 사용하지 않지만 호환성을 위해 유지
    )
    
    # PDF 파일 존재 확인
    if not os.path.exists(config.sample_pdf_path):
        print(f"❌ 테스트 PDF 파일이 없습니다: {config.sample_pdf_path}")
        print("   sample_docs/ 디렉토리에 sample2.pdf 파일을 준비해주세요.")
        return
    
    print(f"📋 테스트 설정:")
    print(f"   - 동시 실행 레벨: {config.concurrent_levels}")
    print(f"   - 각 레벨당 세트 수: 레벨 × 3")
    print(f"   - 테스트 PDF: {config.sample_pdf_path}")
    print(f"   - Workers 설정: 1 (단일 워커)")
    print()
    
    results = []
    
    async with ConcurrentTester(config) as tester:
        for concurrent_level in config.concurrent_levels:
            print(f"🔄 동시 실행 레벨 {concurrent_level} 테스트 중...")
            
            try:
                result = await tester.run_concurrent_set(concurrent_level)
                results.append(result)
                
                # 결과 출력
                print(f"✅ 레벨 {concurrent_level} 완료:")
                print(f"   - 총 요청: {result.total_requests}개")
                print(f"   - 성공: {result.successful_requests}개")
                print(f"   - 실패: {result.failed_requests}개")
                print(f"   - 평균 응답시간: {result.avg_response_time:.2f}초")
                print(f"   - 처리량: {result.requests_per_second:.1f} 요청/초")
                print(f"   - CPU 평균: {result.system_metrics.get('avg_cpu_percent', 0):.1f}%")
                print(f"   - 메모리 평균: {result.system_metrics.get('avg_memory_percent', 0):.1f}%")
                print()
                
            except Exception as e:
                logger.error(f"레벨 {concurrent_level} 테스트 실패: {e}")
                print(f"❌ 레벨 {concurrent_level} 테스트 실패: {e}")
                print()
    
    # 최종 결과 요약
    print("📊 최종 결과 요약:")
    print("-" * 60)
    for result in results:
        success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0
        print(f"레벨 {result.concurrent_level:2d}: "
              f"{result.requests_per_second:6.1f} 요청/초, "
              f"성공률 {success_rate:5.1f}%, "
              f"평균 응답시간 {result.avg_response_time:5.2f}초")
    
    # 최적 성능 찾기
    if results:
        best_result = max(results, key=lambda r: r.requests_per_second)
        print(f"\n🏆 최고 성능: 레벨 {best_result.concurrent_level} - {best_result.requests_per_second:.1f} 요청/초")

if __name__ == "__main__":
    asyncio.run(main())
