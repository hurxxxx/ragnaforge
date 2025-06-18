#!/usr/bin/env python3
"""Clean version of document conversion comparison test."""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def get_test_files(directory="sample_docs"):
    """Get all testable files from the specified directory."""
    test_files = []
    
    if not os.path.exists(directory):
        return test_files
        
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if not os.path.isfile(file_path):
            continue
            
        file_extension = os.path.splitext(file)[1].lower()
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        
        # Determine file type and supported endpoints
        if file_extension == ".pdf":
            file_type = "PDF"
            endpoints = ["marker", "docling", "compare"]
        elif file_extension == ".md":
            file_type = "Markdown"
            endpoints = ["marker", "docling", "text"]
        elif file_extension in [".txt"]:
            file_type = "Text"
            endpoints = ["marker", "docling", "text"]
        elif file_extension in [".docx", ".doc"]:
            file_type = "Word Document"
            endpoints = ["marker", "docling"]
        else:
            file_type = "Other"
            endpoints = []
        
        test_files.append({
            "name": file,
            "path": file_path,
            "size_mb": file_size,
            "type": file_type,
            "extension": file_extension,
            "endpoints": endpoints,
        })
    
    return sorted(test_files, key=lambda x: x["size_mb"])


def select_test_files():
    """Allow user to select test files."""
    test_files = get_test_files()
    
    if not test_files:
        print("❌ sample_docs 폴더에서 파일을 찾을 수 없습니다.")
        return []
    
    print("📁 발견된 파일들:")
    print("=" * 80)
    
    for i, file_info in enumerate(test_files, 1):
        endpoints_str = ", ".join(file_info["endpoints"]) if file_info["endpoints"] else "지원 안함"
        print(f"{i}. {file_info['name']} ({file_info['size_mb']:.2f} MB)")
        print(f"   📄 타입: {file_info['type']} | 🔗 지원 API: {endpoints_str}")
    
    print("=" * 80)
    print("📝 테스트할 파일을 선택하세요 (최대 3개):")
    print("   - 번호를 입력하세요 (예: 1,2,3)")
    print("   - PDF 파일만: 'pdf', 마크다운: 'md', 모든 파일: 'all'")
    print("   - 종료: 'q'")
    
    while True:
        try:
            user_input = input("\n선택: ").strip().lower()
            
            if user_input == "q":
                return []
            elif user_input == "all":
                return test_files[:3]
            elif user_input == "pdf":
                return [f for f in test_files if f["extension"] == ".pdf"][:3]
            elif user_input == "md":
                return [f for f in test_files if f["extension"] == ".md"][:3]
            else:
                # Parse numbers
                if "," in user_input:
                    numbers = [int(x.strip()) for x in user_input.split(",")]
                else:
                    numbers = [int(x) for x in user_input.split()]
                
                if not numbers or len(numbers) > 3:
                    print("❌ 최대 3개 파일만 선택할 수 있습니다.")
                    continue
                
                invalid_numbers = [n for n in numbers if n < 1 or n > len(test_files)]
                if invalid_numbers:
                    print(f"❌ 올바르지 않은 번호: {invalid_numbers}")
                    continue
                
                selected_files = [test_files[n - 1] for n in set(numbers)]
                
                # Check if files are supported
                unsupported = [f for f in selected_files if not f["endpoints"]]
                if unsupported:
                    print("❌ 지원되지 않는 파일이 포함되어 있습니다.")
                    continue
                
                return selected_files
                
        except (ValueError, KeyboardInterrupt):
            print("❌ 올바른 형식으로 입력하세요.")
            if input("계속하시겠습니까? (y/n): ").lower() != 'y':
                return []


def test_marker_conversion(file_info, test_session_dir):
    """Test Marker conversion."""
    if "marker" not in file_info["endpoints"]:
        return None
        
    print("1. 🎯 Marker 변환 테스트...")
    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
        test_data = {
            "file_path": file_info["path"],
            "output_dir": f"{test_session_dir}/marker",
            "extract_images": True,
        }
        
        response = requests.post(f"{BASE_URL}/v1/convert/marker", headers=headers, json=test_data, timeout=300)
        
        print(f"   상태: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if result.get('success', False):
                print(f"   ✅ Marker 변환 성공!")
                print(f"   ⏱️  변환 시간: {result['conversion_time']:.2f}초")
                print(f"   📝 마크다운 길이: {result['markdown_length']:,} 문자")
                print(f"   🖼️  이미지 개수: {result['images_count']}")
                print(f"   💾 저장된 파일: {len(result['saved_files'])}개")
            else:
                print(f"   ❌ Marker 변환 실패!")
                print(f"   ❌ 오류: {result.get('error', '알 수 없는 오류')}")
            return result
        else:
            print(f"   ❌ Marker HTTP 요청 실패: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Marker 테스트 오류: {e}")
        return None


def test_docling_conversion(file_info, test_session_dir):
    """Test Docling conversion."""
    if "docling" not in file_info["endpoints"]:
        return None
        
    print("\n2. 🎯 Docling 변환 테스트...")
    try:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}
        test_data = {
            "file_path": file_info["path"],
            "output_dir": f"{test_session_dir}/docling",
            "extract_images": True,
        }
        
        response = requests.post(f"{BASE_URL}/v1/convert/docling", headers=headers, json=test_data, timeout=300)
        
        print(f"   상태: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if result.get('success', False):
                print(f"   ✅ Docling 변환 성공!")
                print(f"   ⏱️  변환 시간: {result['conversion_time']:.2f}초")
                print(f"   📝 마크다운 길이: {result['markdown_length']:,} 문자")
                print(f"   🖼️  이미지 개수: {result['images_count']}")
                print(f"   💾 저장된 파일: {len(result['saved_files'])}개")
            else:
                print(f"   ❌ Docling 변환 실패!")
                print(f"   ❌ 오류: {result.get('error', '알 수 없는 오류')}")
            return result
        else:
            print(f"   ❌ Docling HTTP 요청 실패: {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Docling 테스트 오류: {e}")
        return None


def test_comparison(file_info, marker_result, docling_result):
    """Compare already converted results locally without additional API calls."""
    if "compare" not in file_info["endpoints"]:
        return None

    marker_success = marker_result and marker_result.get('success', False)
    docling_success = docling_result and docling_result.get('success', False)

    if not (marker_success and docling_success):
        print("\n3. 🔄 로컬 결과 비교...")
        print("   ⚠️  비교 테스트 건너뜀: 한쪽 또는 양쪽 변환이 실패했습니다")
        if not marker_success:
            print("      - Marker 변환 실패")
        if not docling_success:
            print("      - Docling 변환 실패")
        print("   💡 두 라이브러리 모두 성공해야 의미있는 비교가 가능합니다")
        return None

    print("\n3. 🔄 로컬 결과 비교...")
    try:
        # 이미 변환된 결과를 사용해서 로컬에서 비교 수행
        print("   📊 이미 변환된 결과를 활용하여 비교 중...")

        # 속도 비교
        marker_time = marker_result.get('conversion_time', 0)
        docling_time = docling_result.get('conversion_time', 0)

        if marker_time > 0 and docling_time > 0:
            if marker_time < docling_time:
                faster_library = "Marker"
                speed_ratio = docling_time / marker_time
            else:
                faster_library = "Docling"
                speed_ratio = marker_time / docling_time
        else:
            faster_library = "Unknown"
            speed_ratio = None

        # 출력 비교
        marker_length = marker_result.get('markdown_length', 0)
        docling_length = docling_result.get('markdown_length', 0)
        marker_images = marker_result.get('images_count', 0)
        docling_images = docling_result.get('images_count', 0)

        # 리소스 사용량 비교
        marker_gpu = marker_result.get('gpu_memory_used_gb')
        docling_gpu = docling_result.get('gpu_memory_used_gb')

        # 비교 결과 구성
        comparison = {
            "speed_comparison": {
                "marker_time": marker_time,
                "docling_time": docling_time,
                "faster_library": faster_library,
                "speed_ratio": speed_ratio
            },
            "output_comparison": {
                "marker_markdown_length": marker_length,
                "docling_markdown_length": docling_length,
                "marker_images": marker_images,
                "docling_images": docling_images
            },
            "resource_usage": {
                "marker_gpu_memory": marker_gpu,
                "docling_gpu_memory": docling_gpu
            }
        }

        result = {
            "marker_result": marker_result,
            "docling_result": docling_result,
            "comparison": comparison
        }

        print(f"   ✅ 로컬 비교 완료!")
        print(f"      🎯 Marker 시간: {marker_time:.2f}초")
        print(f"      🎯 Docling 시간: {docling_time:.2f}초")
        print(f"      🏆 더 빠른 라이브러리: {faster_library}")
        if speed_ratio:
            print(f"      📈 속도 비율: {speed_ratio:.2f}배")
        print(f"      📝 마크다운 길이 - Marker: {marker_length:,}, Docling: {docling_length:,}")
        print(f"      🖼️  이미지 수 - Marker: {marker_images}, Docling: {docling_images}")

        return result

    except Exception as e:
        print(f"   ❌ 로컬 비교 오류: {e}")
        return None


def generate_simple_report(result, report_file, timestamp):
    """Generate a simple comparison report in markdown format."""
    file_info = result["file_info"]
    test_results = result["test_results"]

    marker_result = test_results.get("marker", {})
    docling_result = test_results.get("docling", {})

    marker_success = marker_result.get('success', False) if marker_result else False
    docling_success = docling_result.get('success', False) if docling_result else False

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# 문서 변환 비교 리포트\n\n")
        f.write(f"**테스트 시간**: {timestamp}\n")
        f.write(f"**파일**: {file_info['name']} ({file_info['size_mb']:.2f} MB)\n\n")

        f.write("## 결과 요약\n\n")
        f.write("| 모듈 | 성공 | 시간(초) | 마크다운 길이 | 이미지 수 | 오류 |\n")
        f.write("|------|------|----------|---------------|-----------|------|\n")

        # Marker row
        if marker_result:
            marker_status = "✅" if marker_success else "❌"
            marker_time = marker_result.get('conversion_time', 0)
            marker_length = marker_result.get('markdown_length', 0)
            marker_images = marker_result.get('images_count', 0)
            marker_error = marker_result.get('error', '-')
            f.write(f"| Marker | {marker_status} | {marker_time:.2f} | {marker_length:,} | {marker_images} | {marker_error} |\n")
        else:
            f.write("| Marker | ❌ | - | - | - | 테스트 안함 |\n")

        # Docling row
        if docling_result:
            docling_status = "✅" if docling_success else "❌"
            docling_time = docling_result.get('conversion_time', 0)
            docling_length = docling_result.get('markdown_length', 0)
            docling_images = docling_result.get('images_count', 0)
            docling_error = docling_result.get('error', '-')
            f.write(f"| Docling | {docling_status} | {docling_time:.2f} | {docling_length:,} | {docling_images} | {docling_error} |\n\n")
        else:
            f.write("| Docling | ❌ | - | - | - | 테스트 안함 |\n\n")

        # Winner
        if marker_success and docling_success:
            marker_time = marker_result.get('conversion_time', 0)
            docling_time = docling_result.get('conversion_time', 0)
            if marker_time < docling_time:
                winner = "Marker"
                ratio = docling_time / marker_time
            else:
                winner = "Docling"
                ratio = marker_time / docling_time
            f.write(f"**🏆 속도 우승**: {winner} ({ratio:.2f}배 빠름)\n\n")
        elif marker_success and not docling_success:
            f.write("**🏆 결과**: Marker만 성공\n\n")
        elif not marker_success and docling_success:
            f.write("**🏆 결과**: Docling만 성공\n\n")
        else:
            f.write("**❌ 결과**: 두 모듈 모두 실패\n\n")

        # File structure
        f.write("## 생성된 파일\n\n")
        f.write("```\n")
        f.write(f"{timestamp}/\n")
        f.write("├── marker/\n")
        if marker_success and marker_result.get('saved_files'):
            f.write("│   └── [Marker 변환 결과 파일들]\n")
        else:
            f.write("│   └── (변환 실패)\n")
        f.write("├── docling/\n")
        if docling_success and docling_result.get('saved_files'):
            f.write("│   └── [Docling 변환 결과 파일들]\n")
        else:
            f.write("│   └── (변환 실패)\n")
        f.write("└── comparison_report.md\n")
        f.write("```\n")


def test_single_file_conversion(file_info, test_session_dir):
    """Test conversion for a single file."""
    print(f"\n📄 테스트 파일: {file_info['name']} ({file_info['size_mb']:.2f} MB)")
    print(f"📄 파일 타입: {file_info['type']}")
    print("=" * 80)

    # Run individual tests
    marker_result = test_marker_conversion(file_info, test_session_dir)
    docling_result = test_docling_conversion(file_info, test_session_dir)
    comparison_result = test_comparison(file_info, marker_result, docling_result)

    # Compile results
    results = {
        "file_info": file_info,
        "test_results": {
            "marker": marker_result,
            "docling": docling_result,
            "comparison": comparison_result
        }
    }

    # Generate simple comparison report in the test session directory
    report_file = Path(test_session_dir) / "comparison_report.md"
    generate_simple_report(results, report_file, test_session_dir.split('/')[-1])

    print(f"\n   💾 결과 저장됨: {test_session_dir}")
    print(f"      📁 marker/ - Marker 모듈 결과")
    print(f"      📁 docling/ - Docling 모듈 결과")
    print(f"      📄 comparison_report.md - 비교 리포트")

    return results


def print_summary(all_results):
    """Print summary of all test results."""
    print("\n" + "=" * 80)
    print("📊 전체 테스트 요약")
    print("=" * 80)

    for i, result in enumerate(all_results, 1):
        file_info = result["file_info"]
        marker_result = result["test_results"].get("marker")
        docling_result = result["test_results"].get("docling")

        print(f"{i}. {file_info['name']} ({file_info['size_mb']:.2f} MB)")

        # Check success status
        marker_success = marker_result and marker_result.get('success', False)
        docling_success = docling_result and docling_result.get('success', False)

        if marker_success:
            print(f"   🎯 Marker: {marker_result['conversion_time']:.2f}초, {marker_result['markdown_length']:,} 문자 ✅")
        elif marker_result:
            print(f"   🎯 Marker: {marker_result['conversion_time']:.2f}초 ❌ ({marker_result.get('error', '알 수 없는 오류')})")

        if docling_success:
            print(f"   🎯 Docling: {docling_result['conversion_time']:.2f}초, {docling_result['markdown_length']:,} 문자 ✅")
        elif docling_result:
            print(f"   🎯 Docling: {docling_result['conversion_time']:.2f}초 ❌ ({docling_result.get('error', '알 수 없는 오류')})")

        # Only compare speed if both were successful
        if marker_success and docling_success:
            if marker_result["conversion_time"] < docling_result["conversion_time"]:
                speed_winner = "Marker"
                speed_ratio = docling_result["conversion_time"] / marker_result["conversion_time"]
            else:
                speed_winner = "Docling"
                speed_ratio = marker_result["conversion_time"] / docling_result["conversion_time"]
            print(f"   🏆 속도 우승자: {speed_winner} ({speed_ratio:.2f}배 빠름)")
        elif marker_success and not docling_success:
            print("   🏆 성공: Marker만 성공")
        elif not marker_success and docling_success:
            print("   🏆 성공: Docling만 성공")
        else:
            print("   ❌ 두 라이브러리 모두 실패")


def main():
    """Main test function."""
    print("🔄 PDF 문서 변환 성능 비교 테스트")
    print("=" * 80)

    # Create timestamped test directory
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    test_session_dir = f"test_outputs/{timestamp}"

    print(f"🔑 API 키: {API_KEY[:20]}...")
    print(f"🌐 기본 URL: {BASE_URL}")
    print(f"📁 테스트 세션 디렉토리: {test_session_dir}")
    print()

    # Create test session directory and module subdirectories
    os.makedirs(test_session_dir, exist_ok=True)
    os.makedirs(f"{test_session_dir}/marker", exist_ok=True)
    os.makedirs(f"{test_session_dir}/docling", exist_ok=True)

    # Select files to test
    selected_files = select_test_files()
    if not selected_files:
        print("❌ 테스트할 파일이 선택되지 않았습니다.")
        return

    print(f"\n✅ {len(selected_files)}개 파일이 선택되었습니다.")
    all_results = []

    # Test each selected file
    for i, file_info in enumerate(selected_files, 1):
        print(f"\n📋 파일 {i}/{len(selected_files)} 테스트 중...")
        result = test_single_file_conversion(file_info, test_session_dir)
        all_results.append(result)

    # Print summary
    print_summary(all_results)

    # Save summary results in the test session directory
    summary_file = Path(test_session_dir) / "test_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

    # Also save latest summary in test_outputs root (for easy access)
    latest_summary_file = Path("test_outputs") / "latest_test_summary.json"
    with open(latest_summary_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n💾 전체 결과가 저장되었습니다:")
    print(f"   📄 테스트 세션: {summary_file}")
    print(f"   📄 최신 결과: {latest_summary_file}")


if __name__ == "__main__":
    main()
