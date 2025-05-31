#!/usr/bin/env python3
"""Simple test script for document conversion functionality."""

import os
import sys
import tempfile
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, '.')

from services.document_conversion_service import DocumentConversionService


def create_sample_html_document():
    """Create a simple HTML document for testing."""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Document</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        h2 { color: #666; }
        .highlight { background-color: yellow; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>문서 변환 테스트</h1>
    
    <h2>개요</h2>
    <p>이 문서는 <span class="highlight">datalab-marker</span>를 사용한 문서 변환 기능을 테스트하기 위한 샘플 문서입니다.</p>
    
    <h2>주요 기능</h2>
    <ul>
        <li>HTML에서 마크다운으로 변환</li>
        <li>이미지 추출 및 저장</li>
        <li>다양한 출력 형식 지원 (markdown, json, html)</li>
        <li>한국어 텍스트 처리</li>
    </ul>
    
    <h2>지원 형식</h2>
    <table>
        <tr>
            <th>입력 형식</th>
            <th>설명</th>
        </tr>
        <tr>
            <td>PDF</td>
            <td>Adobe PDF 문서</td>
        </tr>
        <tr>
            <td>DOCX</td>
            <td>Microsoft Word 문서</td>
        </tr>
        <tr>
            <td>PPTX</td>
            <td>Microsoft PowerPoint 프레젠테이션</td>
        </tr>
        <tr>
            <td>HTML</td>
            <td>웹 페이지 문서</td>
        </tr>
    </table>
    
    <h2>수식 예제</h2>
    <p>간단한 수학 공식: E = mc²</p>
    <p>더 복잡한 수식: ∫₀^∞ e^(-x²) dx = √π/2</p>
    
    <h2>코드 예제</h2>
    <pre><code>
def hello_world():
    print("안녕하세요, 세계!")
    return "Hello, World!"
    </code></pre>
    
    <h2>결론</h2>
    <p>이 테스트 문서를 통해 문서 변환 기능이 올바르게 작동하는지 확인할 수 있습니다.</p>
    
    <footer>
        <p><em>생성일: 2024년</em></p>
    </footer>
</body>
</html>
"""
    return html_content


def test_document_conversion():
    """Test document conversion with a sample HTML file."""
    print("🚀 문서 변환 테스트 시작...")
    
    # Create service instance
    service = DocumentConversionService("test_output")
    print("✓ 문서 변환 서비스 초기화 완료")
    
    # Create sample HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(create_sample_html_document())
        html_file_path = f.name
    
    print(f"✓ 샘플 HTML 문서 생성: {html_file_path}")
    
    try:
        # Test markdown conversion
        print("\n📝 마크다운 변환 테스트...")
        result = service.convert_document(
            file_path=html_file_path,
            output_format="markdown",
            extract_images=True,
            use_llm=False
        )
        
        print(f"✓ 변환 완료!")
        print(f"  - 출력 형식: {result['output_format']}")
        print(f"  - 저장 경로: {result['file_path']}")
        print(f"  - 이미지 개수: {len(result['images'])}")
        print(f"  - 메타데이터 키: {list(result['metadata'].keys())}")
        
        # Show first 500 characters of markdown content
        if result.get('markdown_content'):
            content_preview = result['markdown_content'][:500]
            print(f"\n📄 마크다운 내용 미리보기:")
            print("-" * 50)
            print(content_preview)
            if len(result['markdown_content']) > 500:
                print("...")
            print("-" * 50)
        
        # Test JSON conversion
        print("\n🔧 JSON 변환 테스트...")
        json_result = service.convert_document(
            file_path=html_file_path,
            output_format="json",
            extract_images=False,
            use_llm=False
        )
        
        print(f"✓ JSON 변환 완료!")
        print(f"  - 저장 경로: {json_result['file_path']}")
        print(f"  - JSON 구조 키: {list(json_result.get('json_content', {}).keys())}")
        
        # Test HTML conversion
        print("\n🌐 HTML 변환 테스트...")
        html_result = service.convert_document(
            file_path=html_file_path,
            output_format="html",
            extract_images=False,
            use_llm=False
        )
        
        print(f"✓ HTML 변환 완료!")
        print(f"  - 저장 경로: {html_result['file_path']}")
        
        # Show output directory structure
        print(f"\n📁 출력 디렉토리 구조:")
        output_dir = Path("test_output")
        for subdir in ["markdown", "json", "html", "images"]:
            subdir_path = output_dir / subdir
            if subdir_path.exists():
                files = list(subdir_path.glob("*"))
                print(f"  {subdir}/: {len(files)} 파일")
                for file in files[:3]:  # Show first 3 files
                    print(f"    - {file.name}")
                if len(files) > 3:
                    print(f"    ... 및 {len(files) - 3}개 더")
        
        print("\n🎉 모든 변환 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 변환 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if os.path.exists(html_file_path):
            os.unlink(html_file_path)
        print("✓ 임시 파일 정리 완료")


def test_api_server():
    """Test if the API server can start."""
    print("\n🌐 API 서버 테스트...")
    
    try:
        # Import main app
        from main import app
        print("✓ FastAPI 앱 임포트 성공")
        
        # Check if document conversion endpoint exists
        routes = [route.path for route in app.routes]
        if "/v1/convert" in routes:
            print("✓ /v1/convert 엔드포인트 등록 확인")
        else:
            print("❌ /v1/convert 엔드포인트를 찾을 수 없음")
            return False
        
        print("✓ API 서버 구성 확인 완료")
        return True
        
    except Exception as e:
        print(f"❌ API 서버 테스트 실패: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("📋 DATALAB-MARKER 문서 변환 기능 테스트")
    print("=" * 60)
    
    # Test document conversion
    conversion_success = test_document_conversion()
    
    # Test API server
    api_success = test_api_server()
    
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"문서 변환 테스트: {'✅ 성공' if conversion_success else '❌ 실패'}")
    print(f"API 서버 테스트: {'✅ 성공' if api_success else '❌ 실패'}")
    
    if conversion_success and api_success:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("\n📝 사용 방법:")
        print("1. API 서버 시작: python main.py")
        print("2. 문서 변환 요청: POST /v1/convert")
        print("3. 지원 형식: PDF, DOCX, PPTX, HTML, EPUB 등")
    else:
        print("\n⚠️  일부 테스트가 실패했습니다. 로그를 확인해주세요.")
        sys.exit(1)
