#!/usr/bin/env python3
"""Test document conversion with real PDF and DOCX files from sample_docs/."""

import pytest
import os
import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.document_conversion_service import DocumentConversionService


class TestRealDocumentConversion:
    """Test cases for real document conversion using files from sample_docs/."""

    @pytest.fixture
    def service(self):
        """Create a document conversion service instance for testing."""
        return DocumentConversionService("real_test_output")

    @pytest.fixture
    def sample_files(self):
        """Get paths to sample documents."""
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

    def test_pdf_to_markdown_conversion(self, service, sample_files):
        """Test PDF to markdown conversion with real file."""
        pdf_path = sample_files["pdf"]
        print(f"\n🔄 PDF 변환 테스트: {pdf_path.name}")
        
        start_time = time.time()
        
        result = service.convert_document(
            file_path=str(pdf_path),
            output_format="markdown",
            extract_images=True,
            use_llm=False
        )
        
        conversion_time = time.time() - start_time
        
        # Assertions
        assert result["output_format"] == "markdown"
        assert "markdown_content" in result
        assert result["markdown_content"] is not None
        assert len(result["markdown_content"]) > 0
        assert "file_path" in result
        assert Path(result["file_path"]).exists()
        
        # Print results
        print(f"✅ PDF 변환 완료!")
        print(f"  - 변환 시간: {conversion_time:.2f}초")
        print(f"  - 출력 파일: {result['file_path']}")
        print(f"  - 마크다운 길이: {len(result['markdown_content'])} 문자")
        print(f"  - 추출된 이미지: {len(result.get('images', []))}개")
        print(f"  - 메타데이터 키: {list(result.get('metadata', {}).keys())}")
        
        # Show content preview
        content_preview = result["markdown_content"][:500]
        print(f"\n📄 마크다운 내용 미리보기:")
        print("-" * 60)
        print(content_preview)
        if len(result["markdown_content"]) > 500:
            print("...")
        print("-" * 60)

    def test_docx_to_markdown_conversion(self, service, sample_files):
        """Test DOCX to markdown conversion with real file."""
        docx_path = sample_files["docx"]
        print(f"\n🔄 DOCX 변환 테스트: {docx_path.name}")
        
        start_time = time.time()
        
        result = service.convert_document(
            file_path=str(docx_path),
            output_format="markdown",
            extract_images=True,
            use_llm=False
        )
        
        conversion_time = time.time() - start_time
        
        # Assertions
        assert result["output_format"] == "markdown"
        assert "markdown_content" in result
        assert result["markdown_content"] is not None
        assert len(result["markdown_content"]) > 0
        assert "file_path" in result
        assert Path(result["file_path"]).exists()
        
        # Print results
        print(f"✅ DOCX 변환 완료!")
        print(f"  - 변환 시간: {conversion_time:.2f}초")
        print(f"  - 출력 파일: {result['file_path']}")
        print(f"  - 마크다운 길이: {len(result['markdown_content'])} 문자")
        print(f"  - 추출된 이미지: {len(result.get('images', []))}개")
        print(f"  - 메타데이터 키: {list(result.get('metadata', {}).keys())}")
        
        # Show content preview
        content_preview = result["markdown_content"][:500]
        print(f"\n📄 마크다운 내용 미리보기:")
        print("-" * 60)
        print(content_preview)
        if len(result["markdown_content"]) > 500:
            print("...")
        print("-" * 60)

    def test_pdf_to_json_conversion(self, service, sample_files):
        """Test PDF to JSON conversion with real file."""
        pdf_path = sample_files["pdf"]
        print(f"\n🔄 PDF → JSON 변환 테스트: {pdf_path.name}")
        
        start_time = time.time()
        
        result = service.convert_document(
            file_path=str(pdf_path),
            output_format="json",
            extract_images=False,
            use_llm=False
        )
        
        conversion_time = time.time() - start_time
        
        # Assertions
        assert result["output_format"] == "json"
        assert "json_content" in result
        assert result["json_content"] is not None
        assert "file_path" in result
        assert Path(result["file_path"]).exists()
        
        # Print results
        print(f"✅ PDF → JSON 변환 완료!")
        print(f"  - 변환 시간: {conversion_time:.2f}초")
        print(f"  - 출력 파일: {result['file_path']}")
        print(f"  - JSON 구조 키: {list(result['json_content'].keys())}")

    def test_docx_to_html_conversion(self, service, sample_files):
        """Test DOCX to HTML conversion with real file."""
        docx_path = sample_files["docx"]
        print(f"\n🔄 DOCX → HTML 변환 테스트: {docx_path.name}")
        
        start_time = time.time()
        
        result = service.convert_document(
            file_path=str(docx_path),
            output_format="html",
            extract_images=False,
            use_llm=False
        )
        
        conversion_time = time.time() - start_time
        
        # Assertions
        assert result["output_format"] == "html"
        assert "html_content" in result
        assert result["html_content"] is not None
        assert len(result["html_content"]) > 0
        assert "file_path" in result
        assert Path(result["file_path"]).exists()
        
        # Print results
        print(f"✅ DOCX → HTML 변환 완료!")
        print(f"  - 변환 시간: {conversion_time:.2f}초")
        print(f"  - 출력 파일: {result['file_path']}")
        print(f"  - HTML 길이: {len(result['html_content'])} 문자")

    def test_conversion_with_llm(self, service, sample_files):
        """Test conversion with LLM enhancement (requires API key)."""
        pdf_path = sample_files["pdf"]
        print(f"\n🤖 LLM 향상 변환 테스트: {pdf_path.name}")
        
        # This test will be skipped if no LLM API key is configured
        try:
            start_time = time.time()
            
            result = service.convert_document(
                file_path=str(pdf_path),
                output_format="markdown",
                extract_images=True,
                use_llm=True  # Enable LLM enhancement
            )
            
            conversion_time = time.time() - start_time
            
            # Assertions
            assert result["output_format"] == "markdown"
            assert "markdown_content" in result
            assert result["markdown_content"] is not None
            
            print(f"✅ LLM 향상 변환 완료!")
            print(f"  - 변환 시간: {conversion_time:.2f}초")
            print(f"  - 마크다운 길이: {len(result['markdown_content'])} 문자")
            print("  - LLM 향상 기능이 적용되었습니다.")
            
        except Exception as e:
            if "API key" in str(e) or "authentication" in str(e).lower():
                pytest.skip(f"LLM API 키가 설정되지 않음: {str(e)}")
            else:
                raise

    def test_performance_comparison(self, service, sample_files):
        """Compare conversion performance between different formats."""
        pdf_path = sample_files["pdf"]
        print(f"\n⚡ 성능 비교 테스트: {pdf_path.name}")
        
        formats = ["markdown", "json", "html"]
        results = {}
        
        for format_type in formats:
            print(f"  🔄 {format_type.upper()} 변환 중...")
            start_time = time.time()
            
            result = service.convert_document(
                file_path=str(pdf_path),
                output_format=format_type,
                extract_images=False,  # Disable for fair comparison
                use_llm=False
            )
            
            conversion_time = time.time() - start_time
            results[format_type] = {
                "time": conversion_time,
                "output_size": len(str(result.get(f"{format_type}_content", "")))
            }
            
            print(f"    ✅ 완료: {conversion_time:.2f}초")
        
        # Print comparison results
        print(f"\n📊 성능 비교 결과:")
        print("-" * 50)
        for format_type, data in results.items():
            print(f"{format_type.upper():>8}: {data['time']:>6.2f}초, {data['output_size']:>8} 문자")
        print("-" * 50)
        
        # Find fastest format
        fastest = min(results.items(), key=lambda x: x[1]["time"])
        print(f"🏆 가장 빠른 형식: {fastest[0].upper()} ({fastest[1]['time']:.2f}초)")


if __name__ == "__main__":
    """Direct execution for manual testing."""
    print("=" * 80)
    print("🧪 실제 문서 변환 테스트 (sample_docs/ 파일 사용)")
    print("=" * 80)
    
    # Initialize service
    service = DocumentConversionService("manual_test_output")
    
    # Check sample files
    sample_dir = Path("sample_docs")
    if not sample_dir.exists():
        print("❌ sample_docs/ 디렉토리를 찾을 수 없습니다.")
        sys.exit(1)
    
    pdf_file = sample_dir / "P02_01_01_001_20210101.pdf"
    docx_file = sample_dir / "멀티 에이전트 시스템 개발 계획_.docx"
    
    files_to_test = []
    if pdf_file.exists():
        files_to_test.append(("PDF", pdf_file))
    if docx_file.exists():
        files_to_test.append(("DOCX", docx_file))
    
    if not files_to_test:
        print("❌ 테스트할 파일을 찾을 수 없습니다.")
        print("   필요한 파일: P02_01_01_001_20210101.pdf, 멀티 에이전트 시스템 개발 계획_.docx")
        sys.exit(1)
    
    print(f"📁 발견된 파일: {len(files_to_test)}개")
    for file_type, file_path in files_to_test:
        print(f"  - {file_type}: {file_path.name}")
    
    print("\n" + "=" * 80)
    print("⚠️  실제 테스트 실행을 원하시면 다음 명령을 사용하세요:")
    print("PYTHONPATH=. python -m pytest tests/test_real_document_conversion.py -v -s")
    print("=" * 80)
