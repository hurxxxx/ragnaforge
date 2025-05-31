#!/usr/bin/env python3
"""Simple API client test for document conversion endpoint."""

import requests
import tempfile
import os
import json
from pathlib import Path


def create_test_html():
    """Create a simple test HTML file."""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>API 테스트 문서</title>
</head>
<body>
    <h1>API 테스트</h1>
    <p>이것은 <strong>datalab-marker</strong> API 테스트를 위한 간단한 HTML 문서입니다.</p>
    
    <h2>기능 목록</h2>
    <ul>
        <li>HTML을 마크다운으로 변환</li>
        <li>이미지 추출</li>
        <li>다양한 출력 형식 지원</li>
    </ul>
    
    <h2>테이블 예제</h2>
    <table border="1">
        <tr>
            <th>항목</th>
            <th>설명</th>
        </tr>
        <tr>
            <td>입력</td>
            <td>HTML 파일</td>
        </tr>
        <tr>
            <td>출력</td>
            <td>마크다운 텍스트</td>
        </tr>
    </table>
    
    <p><em>테스트 완료!</em></p>
</body>
</html>
"""
    return html_content


def test_convert_api(base_url="http://localhost:8000"):
    """Test the document conversion API."""
    print("🚀 API 변환 테스트 시작...")
    
    # Create test HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(create_test_html())
        html_file_path = f.name
    
    try:
        # Test markdown conversion
        print("\n📝 마크다운 변환 API 테스트...")
        
        with open(html_file_path, 'rb') as f:
            files = {'file': ('test.html', f, 'text/html')}
            data = {
                'output_format': 'markdown',
                'extract_images': True,
                'use_llm': False
            }
            
            response = requests.post(f"{base_url}/v1/convert", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 마크다운 변환 성공!")
            print(f"  - 출력 형식: {result.get('output_format')}")
            print(f"  - 파일 경로: {result.get('file_path')}")
            print(f"  - 이미지 개수: {len(result.get('images', []))}")
            
            # Show markdown content preview
            if result.get('markdown_content'):
                content = result['markdown_content'][:300]
                print(f"\n📄 마크다운 내용 미리보기:")
                print("-" * 40)
                print(content)
                if len(result['markdown_content']) > 300:
                    print("...")
                print("-" * 40)
        else:
            print(f"❌ 마크다운 변환 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False
        
        # Test JSON conversion
        print("\n🔧 JSON 변환 API 테스트...")
        
        with open(html_file_path, 'rb') as f:
            files = {'file': ('test.html', f, 'text/html')}
            data = {
                'output_format': 'json',
                'extract_images': False,
                'use_llm': False
            }
            
            response = requests.post(f"{base_url}/v1/convert", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ JSON 변환 성공!")
            print(f"  - 파일 경로: {result.get('file_path')}")
            if result.get('json_content'):
                print(f"  - JSON 구조 키: {list(result['json_content'].keys())}")
        else:
            print(f"❌ JSON 변환 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False
        
        # Test unsupported format
        print("\n⚠️  지원하지 않는 형식 테스트...")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("test content")
            unsupported_file = f.name
        
        try:
            with open(unsupported_file, 'rb') as f:
                files = {'file': ('test.xyz', f, 'application/octet-stream')}
                data = {'output_format': 'markdown'}
                
                response = requests.post(f"{base_url}/v1/convert", files=files, data=data)
            
            if response.status_code == 400:
                print("✅ 지원하지 않는 형식 에러 처리 성공!")
            else:
                print(f"⚠️  예상과 다른 응답: {response.status_code}")
        finally:
            os.unlink(unsupported_file)
        
        print("\n🎉 모든 API 테스트 완료!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ API 서버에 연결할 수 없습니다.")
        print("   서버가 실행 중인지 확인해주세요: python main.py")
        return False
    except Exception as e:
        print(f"❌ API 테스트 중 오류 발생: {str(e)}")
        return False
    finally:
        # Cleanup
        if os.path.exists(html_file_path):
            os.unlink(html_file_path)


def test_health_endpoint(base_url="http://localhost:8000"):
    """Test the health endpoint."""
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ 헬스 체크 성공: {health_data}")
            return True
        else:
            print(f"❌ 헬스 체크 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 헬스 체크 오류: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🌐 DATALAB-MARKER API 클라이언트 테스트")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    print("🏥 헬스 체크...")
    health_ok = test_health_endpoint(base_url)
    
    if health_ok:
        # Test conversion API
        api_ok = test_convert_api(base_url)
        
        print("\n" + "=" * 60)
        print("📊 테스트 결과")
        print("=" * 60)
        print(f"헬스 체크: {'✅ 성공' if health_ok else '❌ 실패'}")
        print(f"변환 API: {'✅ 성공' if api_ok else '❌ 실패'}")
        
        if health_ok and api_ok:
            print("\n🎉 모든 API 테스트가 성공했습니다!")
            print("\n📝 사용 예제:")
            print("curl -X POST http://localhost:8000/v1/convert \\")
            print("  -F 'file=@document.pdf' \\")
            print("  -F 'output_format=markdown' \\")
            print("  -F 'extract_images=true'")
        else:
            print("\n⚠️  일부 테스트가 실패했습니다.")
    else:
        print("\n❌ 서버가 실행되지 않았거나 응답하지 않습니다.")
        print("다음 명령으로 서버를 시작하세요:")
        print("python main.py")
