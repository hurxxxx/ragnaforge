#!/usr/bin/env python3
"""Test document conversion API with real PDF and DOCX files from sample_docs/."""

import pytest
import requests
import time
import json
from pathlib import Path


class TestRealDocumentConversionAPI:
    """Test cases for real document conversion API using files from sample_docs/."""

    @pytest.fixture
    def base_url(self):
        """API base URL."""
        return "http://localhost:8000"

    @pytest.fixture
    def sample_files(self):
        """Get paths to sample documents."""
        project_root = Path(__file__).parent.parent
        sample_dir = project_root / "sample_docs"
        
        files = {
            "pdf": sample_dir / "P02_01_01_001_20210101.pdf",
            "docx": sample_dir / "멀티 에이전트 시스템 개발 계획_.docx"
        }
        
        # Verify files exist
        for file_type, file_path in files.items():
            if not file_path.exists():
                pytest.skip(f"Sample {file_type} file not found: {file_path}")
        
        return files

    def test_api_health_check(self, base_url):
        """Test API health endpoint before running conversion tests."""
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            assert response.status_code == 200
            health_data = response.json()
            assert health_data["status"] == "healthy"
            print(f"✅ API 헬스 체크 성공: {health_data}")
        except requests.exceptions.ConnectionError:
            pytest.skip("API 서버가 실행되지 않음. 'python main.py'로 서버를 시작하세요.")

    def test_pdf_conversion_api(self, base_url, sample_files):
        """Test PDF conversion via API."""
        pdf_path = sample_files["pdf"]
        print(f"\n🔄 PDF API 변환 테스트: {pdf_path.name}")
        
        start_time = time.time()
        
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
            data = {
                'output_format': 'markdown',
                'extract_images': True,
                'use_llm': False
            }
            
            response = requests.post(f"{base_url}/v1/convert", files=files, data=data, timeout=300)
        
        conversion_time = time.time() - start_time
        
        # Assertions
        assert response.status_code == 200
        result = response.json()
        assert result["output_format"] == "markdown"
        assert "markdown_content" in result
        assert result["markdown_content"] is not None
        assert len(result["markdown_content"]) > 0
        
        # Print results
        print(f"✅ PDF API 변환 완료!")
        print(f"  - 변환 시간: {conversion_time:.2f}초")
        print(f"  - 응답 크기: {len(response.content)} 바이트")
        print(f"  - 마크다운 길이: {len(result['markdown_content'])} 문자")
        print(f"  - 추출된 이미지: {len(result.get('images', []))}개")
        print(f"  - 저장된 파일: {result.get('file_path', 'N/A')}")
        
        # Show content preview
        content_preview = result["markdown_content"][:300]
        print(f"\n📄 마크다운 내용 미리보기:")
        print("-" * 50)
        print(content_preview)
        if len(result["markdown_content"]) > 300:
            print("...")
        print("-" * 50)

    def test_docx_conversion_api(self, base_url, sample_files):
        """Test DOCX conversion via API."""
        docx_path = sample_files["docx"]
        print(f"\n🔄 DOCX API 변환 테스트: {docx_path.name}")
        
        start_time = time.time()
        
        with open(docx_path, 'rb') as f:
            files = {'file': (docx_path.name, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            data = {
                'output_format': 'markdown',
                'extract_images': True,
                'use_llm': False
            }
            
            response = requests.post(f"{base_url}/v1/convert", files=files, data=data, timeout=300)
        
        conversion_time = time.time() - start_time
        
        # Assertions
        assert response.status_code == 200
        result = response.json()
        assert result["output_format"] == "markdown"
        assert "markdown_content" in result
        assert result["markdown_content"] is not None
        assert len(result["markdown_content"]) > 0
        
        # Print results
        print(f"✅ DOCX API 변환 완료!")
        print(f"  - 변환 시간: {conversion_time:.2f}초")
        print(f"  - 응답 크기: {len(response.content)} 바이트")
        print(f"  - 마크다운 길이: {len(result['markdown_content'])} 문자")
        print(f"  - 추출된 이미지: {len(result.get('images', []))}개")
        print(f"  - 저장된 파일: {result.get('file_path', 'N/A')}")
        
        # Show content preview
        content_preview = result["markdown_content"][:300]
        print(f"\n📄 마크다운 내용 미리보기:")
        print("-" * 50)
        print(content_preview)
        if len(result["markdown_content"]) > 300:
            print("...")
        print("-" * 50)

    def test_json_output_format_api(self, base_url, sample_files):
        """Test JSON output format via API."""
        pdf_path = sample_files["pdf"]
        print(f"\n🔧 JSON 출력 형식 API 테스트: {pdf_path.name}")
        
        start_time = time.time()
        
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
            data = {
                'output_format': 'json',
                'extract_images': False,
                'use_llm': False
            }
            
            response = requests.post(f"{base_url}/v1/convert", files=files, data=data, timeout=300)
        
        conversion_time = time.time() - start_time
        
        # Assertions
        assert response.status_code == 200
        result = response.json()
        assert result["output_format"] == "json"
        assert "json_content" in result
        assert result["json_content"] is not None
        
        # Print results
        print(f"✅ JSON API 변환 완료!")
        print(f"  - 변환 시간: {conversion_time:.2f}초")
        print(f"  - JSON 구조 키: {list(result['json_content'].keys())}")
        print(f"  - 저장된 파일: {result.get('file_path', 'N/A')}")

    def test_html_output_format_api(self, base_url, sample_files):
        """Test HTML output format via API."""
        docx_path = sample_files["docx"]
        print(f"\n🌐 HTML 출력 형식 API 테스트: {docx_path.name}")
        
        start_time = time.time()
        
        with open(docx_path, 'rb') as f:
            files = {'file': (docx_path.name, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            data = {
                'output_format': 'html',
                'extract_images': False,
                'use_llm': False
            }
            
            response = requests.post(f"{base_url}/v1/convert", files=files, data=data, timeout=300)
        
        conversion_time = time.time() - start_time
        
        # Assertions
        assert response.status_code == 200
        result = response.json()
        assert result["output_format"] == "html"
        assert "html_content" in result
        assert result["html_content"] is not None
        assert len(result["html_content"]) > 0
        
        # Print results
        print(f"✅ HTML API 변환 완료!")
        print(f"  - 변환 시간: {conversion_time:.2f}초")
        print(f"  - HTML 길이: {len(result['html_content'])} 문자")
        print(f"  - 저장된 파일: {result.get('file_path', 'N/A')}")

    def test_error_handling_api(self, base_url):
        """Test API error handling with unsupported file format."""
        print(f"\n⚠️  에러 핸들링 API 테스트")
        
        # Create a fake file with unsupported extension
        fake_content = b"This is not a real document file"
        
        files = {'file': ('test.xyz', fake_content, 'application/octet-stream')}
        data = {'output_format': 'markdown'}
        
        response = requests.post(f"{base_url}/v1/convert", files=files, data=data, timeout=30)
        
        # Should return 400 Bad Request for unsupported format
        assert response.status_code == 400
        error_data = response.json()
        assert "detail" in error_data
        assert "Unsupported file format" in error_data["detail"]
        
        print(f"✅ 에러 핸들링 테스트 성공!")
        print(f"  - 상태 코드: {response.status_code}")
        print(f"  - 에러 메시지: {error_data['detail']}")

    def test_performance_comparison_api(self, base_url, sample_files):
        """Compare API performance between PDF and DOCX conversion."""
        print(f"\n⚡ API 성능 비교 테스트")
        
        results = {}
        
        for file_type, file_path in sample_files.items():
            print(f"  🔄 {file_type.upper()} 변환 중...")
            start_time = time.time()
            
            mime_types = {
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            }
            
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, mime_types[file_type])}
                data = {
                    'output_format': 'markdown',
                    'extract_images': False,  # Disable for fair comparison
                    'use_llm': False
                }
                
                response = requests.post(f"{base_url}/v1/convert", files=files, data=data, timeout=300)
            
            conversion_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                results[file_type] = {
                    "time": conversion_time,
                    "output_size": len(result.get("markdown_content", "")),
                    "file_size": file_path.stat().st_size
                }
                print(f"    ✅ 완료: {conversion_time:.2f}초")
            else:
                print(f"    ❌ 실패: {response.status_code}")
        
        # Print comparison results
        if results:
            print(f"\n📊 API 성능 비교 결과:")
            print("-" * 70)
            print(f"{'형식':>6} | {'파일크기':>10} | {'변환시간':>8} | {'출력크기':>10} | {'처리속도':>12}")
            print("-" * 70)
            
            for file_type, data in results.items():
                file_size_mb = data["file_size"] / (1024 * 1024)
                processing_speed = file_size_mb / data["time"] if data["time"] > 0 else 0
                
                print(f"{file_type.upper():>6} | {file_size_mb:>8.2f}MB | {data['time']:>6.2f}초 | {data['output_size']:>8} 문자 | {processing_speed:>8.2f}MB/s")
            
            print("-" * 70)


if __name__ == "__main__":
    """Direct execution for manual testing."""
    print("=" * 80)
    print("🌐 실제 문서 변환 API 테스트 (sample_docs/ 파일 사용)")
    print("=" * 80)
    
    # Check if API server is running
    base_url = "http://localhost:8000"
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API 서버가 실행 중입니다.")
        else:
            print(f"⚠️  API 서버 응답 이상: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ API 서버에 연결할 수 없습니다.")
        print("   다음 명령으로 서버를 시작하세요: python main.py")
        exit(1)
    
    # Check sample files
    project_root = Path(__file__).parent.parent
    sample_dir = project_root / "sample_docs"
    
    if not sample_dir.exists():
        print("❌ sample_docs/ 디렉토리를 찾을 수 없습니다.")
        exit(1)
    
    pdf_file = sample_dir / "P02_01_01_001_20210101.pdf"
    docx_file = sample_dir / "멀티 에이전트 시스템 개발 계획_.docx"
    
    files_to_test = []
    if pdf_file.exists():
        files_to_test.append(("PDF", pdf_file))
    if docx_file.exists():
        files_to_test.append(("DOCX", docx_file))
    
    if not files_to_test:
        print("❌ 테스트할 파일을 찾을 수 없습니다.")
        exit(1)
    
    print(f"📁 발견된 파일: {len(files_to_test)}개")
    for file_type, file_path in files_to_test:
        file_size = file_path.stat().st_size / (1024 * 1024)
        print(f"  - {file_type}: {file_path.name} ({file_size:.2f}MB)")
    
    print("\n" + "=" * 80)
    print("⚠️  실제 API 테스트 실행을 원하시면 다음 명령을 사용하세요:")
    print("PYTHONPATH=. python -m pytest tests/test_real_api_conversion.py -v -s")
    print("=" * 80)
