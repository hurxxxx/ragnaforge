#!/usr/bin/env python3
"""Test script for comparing marker and docling PDF conversion performance."""

import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_test_files(directory):
    """Get all testable files from the specified directory."""
    test_files = []
    supported_extensions = [".pdf", ".md", ".txt", ".docx", ".doc"]

    if os.path.exists(directory):
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                file_extension = os.path.splitext(file)[1].lower()
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB

                # Determine file type and API endpoint
                if file_extension == ".pdf":
                    file_type = "PDF"
                    endpoints = ["marker", "docling", "compare"]
                elif file_extension == ".md":
                    file_type = "Markdown"
                    endpoints = ["marker", "docling", "text"]  # Marker도 마크다운 지원
                elif file_extension in [".txt"]:
                    file_type = "Text"
                    endpoints = ["marker", "docling", "text"]  # Marker도 텍스트 지원
                elif file_extension in [".docx", ".doc"]:
                    file_type = "Word Document"
                    endpoints = ["marker", "docling"]  # 둘 다 Word 문서 지원
                else:
                    file_type = "Other"
                    endpoints = []

                test_files.append(
                    {
                        "name": file,
                        "path": file_path,
                        "size_mb": file_size,
                        "type": file_type,
                        "extension": file_extension,
                        "endpoints": endpoints,
                    }
                )

    return sorted(test_files, key=lambda x: x["size_mb"])


def select_test_files():
    """Allow user to select up to 3 files for testing."""
    sample_dir = "sample_docs"
    test_files = get_test_files(sample_dir)

    if not test_files:
        print(f"❌ {sample_dir} 폴더에서 파일을 찾을 수 없습니다.")
        return []

    print(f"📁 {sample_dir} 폴더에서 발견된 파일들:")
    print("=" * 80)

    for i, file_info in enumerate(test_files, 1):
        endpoints_str = (
            ", ".join(file_info["endpoints"]) if file_info["endpoints"] else "지원 안함"
        )
        print(f"{i}. {file_info['name']} ({file_info['size_mb']:.2f} MB)")
        print(f"   📄 타입: {file_info['type']} | 🔗 지원 API: {endpoints_str}")

    print("=" * 80)
    print("📝 테스트할 파일을 선택하세요 (최대 3개):")
    print("   - 번호를 입력하세요 (예: 1,2,3 또는 1 2 3)")
    print("   - PDF 파일만 선택하려면 'pdf' 입력")
    print("   - 마크다운 파일만 선택하려면 'md' 입력")
    print("   - 텍스트 파일만 선택하려면 'txt' 입력")
    print("   - 모든 파일을 선택하려면 'all' 입력")
    print("   - 종료하려면 'q' 입력")

    while True:
        try:
            user_input = input("\n선택: ").strip().lower()

            if user_input == "q":
                return []

            if user_input == "all":
                selected_files = test_files[:3]  # 최대 3개만
                break

            if user_input == "pdf":
                pdf_files = [f for f in test_files if f["extension"] == ".pdf"]
                selected_files = pdf_files[:3]  # 최대 3개만
                if not pdf_files:
                    print("❌ PDF 파일이 없습니다.")
                    continue
                break

            if user_input == "md":
                md_files = [f for f in test_files if f["extension"] == ".md"]
                selected_files = md_files[:3]  # 최대 3개만
                if not md_files:
                    print("❌ 마크다운 파일이 없습니다.")
                    continue
                break

            if user_input == "txt":
                txt_files = [f for f in test_files if f["extension"] == ".txt"]
                selected_files = txt_files[:3]  # 최대 3개만
                if not txt_files:
                    print("❌ 텍스트 파일이 없습니다.")
                    continue
                break

            # 번호 파싱
            if "," in user_input:
                numbers = [int(x.strip()) for x in user_input.split(",")]
            else:
                numbers = [int(x) for x in user_input.split()]

            # 유효성 검사
            if not numbers:
                print("❌ 올바른 번호를 입력하세요.")
                continue

            if len(numbers) > 3:
                print("❌ 최대 3개 파일만 선택할 수 있습니다.")
                continue

            invalid_numbers = [n for n in numbers if n < 1 or n > len(test_files)]
            if invalid_numbers:
                print(f"❌ 올바르지 않은 번호: {invalid_numbers}")
                continue

            # 중복 제거
            numbers = list(set(numbers))
            selected_files = [test_files[n - 1] for n in numbers]

            # 지원되지 않는 파일 확인
            unsupported_files = [f for f in selected_files if not f["endpoints"]]
            if unsupported_files:
                print(f"❌ 지원되지 않는 파일이 포함되어 있습니다:")
                for f in unsupported_files:
                    print(f"   - {f['name']} ({f['type']})")
                continue

            break

        except ValueError:
            print("❌ 올바른 형식으로 입력하세요 (예: 1,2,3)")
        except KeyboardInterrupt:
            print("\n\n❌ 테스트가 취소되었습니다.")
            return []

    print(f"\n✅ 선택된 파일 ({len(selected_files)}개):")
    for i, file_info in enumerate(selected_files, 1):
        endpoints_str = ", ".join(file_info["endpoints"])
        print(f"   {i}. {file_info['name']} ({file_info['size_mb']:.2f} MB)")
        print(f"      📄 타입: {file_info['type']} | 🔗 테스트 API: {endpoints_str}")

    return selected_files


def test_single_file_conversion(file_info, api_key, base_url, output_dir):
    """Test conversion for a single file."""
    print(f"\n📄 테스트 파일: {file_info['name']} ({file_info['size_mb']:.2f} MB)")
    print(f"📄 파일 타입: {file_info['type']}")
    print("=" * 80)

    # Headers
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    # Test data
    test_data = {
        "file_path": file_info["path"],
        "output_dir": output_dir,
        "extract_images": True,
    }

    results = {"file_info": file_info, "test_results": {}}

    # Test 1: Marker conversion (모든 지원되는 파일 타입)
    if "marker" in file_info["endpoints"]:
        print("1. 🎯 Marker 변환 테스트...")
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/v1/convert/marker",
                headers=headers,
                json=test_data,
                timeout=300,
            )

            print(f"   상태: {response.status_code}")
            if response.status_code == 200:
                marker_result = response.json()
                results["test_results"]["marker"] = marker_result
                print(f"   ✅ Marker 변환 성공!")
                print(f"   ⏱️  변환 시간: {marker_result['conversion_time']:.2f}초")
                print(f"   📊 파일 크기: {marker_result['file_size_mb']:.2f} MB")
                print(f"   📝 마크다운 길이: {marker_result['markdown_length']:,} 문자")
                print(f"   🖼️  이미지 개수: {marker_result['images_count']}")
                if marker_result.get("gpu_memory_used_gb"):
                    print(
                        f"   🎮 GPU 메모리 사용: {marker_result['gpu_memory_used_gb']:.2f} GB"
                    )
                print(f"   💾 저장된 파일: {len(marker_result['saved_files'])}개")
            else:
                print(f"   ❌ Marker 변환 실패: {response.text}")
        except Exception as e:
            print(f"   ❌ Marker 테스트 오류: {e}")

    # Test 2: Docling conversion (모든 지원되는 파일 타입)
    if "docling" in file_info["endpoints"]:
        print("\n2. 🎯 Docling 변환 테스트...")
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/v1/convert/docling",
                headers=headers,
                json=test_data,
                timeout=300,
            )

            print(f"   상태: {response.status_code}")
            if response.status_code == 200:
                docling_result = response.json()
                results["test_results"]["docling"] = docling_result
                print(f"   ✅ Docling 변환 성공!")
                print(f"   ⏱️  변환 시간: {docling_result['conversion_time']:.2f}초")
                print(f"   📊 파일 크기: {docling_result['file_size_mb']:.2f} MB")
                print(
                    f"   📝 마크다운 길이: {docling_result['markdown_length']:,} 문자"
                )
                print(f"   🖼️  이미지 개수: {docling_result['images_count']}")
                if docling_result.get("gpu_memory_used_gb"):
                    print(
                        f"   🎮 GPU 메모리 사용: {docling_result['gpu_memory_used_gb']:.2f} GB"
                    )
                print(f"   💾 저장된 파일: {len(docling_result['saved_files'])}개")
            else:
                print(f"   ❌ Docling 변환 실패: {response.text}")
        except Exception as e:
            print(f"   ❌ Docling 테스트 오류: {e}")

    # Test 3: Direct comparison (PDF 파일 또는 비교 지원 파일)
    if "compare" in file_info["endpoints"]:
        print("\n3. 🔄 직접 비교 API 테스트...")
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/v1/convert/compare",
                headers=headers,
                json=test_data,
                timeout=600,
            )

            print(f"   상태: {response.status_code}")
            if response.status_code == 200:
                comparison_result = response.json()
                results["test_results"]["comparison"] = comparison_result
                print(f"   ✅ 비교 완료!")

                # Display comparison results
                comp = comparison_result["comparison"]
                print()
                print("   📊 성능 비교:")
                print(
                    f"      🎯 Marker 시간: {comp['speed_comparison']['marker_time']:.2f}초"
                )
                print(
                    f"      🎯 Docling 시간: {comp['speed_comparison']['docling_time']:.2f}초"
                )
                print(
                    f"      🏆 더 빠른 라이브러리: {comp['speed_comparison']['faster_library']}"
                )
                if comp["speed_comparison"]["speed_ratio"]:
                    print(
                        f"      📈 속도 비율: {comp['speed_comparison']['speed_ratio']:.2f}배"
                    )

                print()
                print("   📝 출력 비교:")
                print(
                    f"      📄 Marker 마크다운: {comp['output_comparison']['marker_markdown_length']:,} 문자"
                )
                print(
                    f"      📄 Docling 마크다운: {comp['output_comparison']['docling_markdown_length']:,} 문자"
                )
                print(
                    f"      🖼️  Marker 이미지: {comp['output_comparison']['marker_images']}"
                )
                print(
                    f"      🖼️  Docling 이미지: {comp['output_comparison']['docling_images']}"
                )

            else:
                print(f"   ❌ 비교 실패: {response.text}")
        except Exception as e:
            print(f"   ❌ 비교 테스트 오류: {e}")

    # Test 4: 기본 텍스트 분석 (로컬 처리)
    if "text" in file_info["endpoints"]:
        test_number = (
            len(
                [
                    e
                    for e in file_info["endpoints"]
                    if e in ["marker", "docling", "compare"]
                ]
            )
            + 1
        )
        print(f"\n{test_number}. 📝 로컬 텍스트 분석...")
        try:
            # 파일 내용 읽기
            with open(file_info["path"], "r", encoding="utf-8") as f:
                content = f.read()

            # 간단한 분석 결과 생성
            text_result = {
                "file_path": file_info["path"],
                "file_size_mb": file_info["size_mb"],
                "content_length": len(content),
                "line_count": len(content.split("\n")),
                "word_count": len(content.split()),
                "processing_time": 0.1,  # 텍스트 파일은 빠르게 처리
                "content_preview": (
                    content[:500] + "..." if len(content) > 500 else content
                ),
            }

            results["test_results"]["text_analysis"] = text_result
            print(f"   ✅ 텍스트 분석 완료!")
            print(f"   📊 파일 크기: {text_result['file_size_mb']:.2f} MB")
            print(f"   📝 내용 길이: {text_result['content_length']:,} 문자")
            print(f"   📄 라인 수: {text_result['line_count']:,} 줄")
            print(f"   🔤 단어 수: {text_result['word_count']:,} 단어")

        except Exception as e:
            print(f"   ❌ 텍스트 분석 오류: {e}")

    return results


def test_document_conversion_comparison():
    """Test and compare marker vs docling PDF conversion performance."""

    print("🔄 PDF 문서 변환 성능 비교 테스트")
    print("=" * 80)

    # Configuration
    api_key = os.getenv("API_KEY", "sk-kure-v1-test-key-12345")
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    output_dir = "test_outputs/conversion_comparison"

    print(f"🔑 API 키: {api_key[:20]}...")
    print(f"🌐 기본 URL: {base_url}")
    print(f"📁 출력 디렉토리: {output_dir}")
    print()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Select test files
    selected_files = select_test_files()
    if not selected_files:
        print("❌ 선택된 파일이 없습니다. 테스트를 종료합니다.")
        return

    print(f"\n🧪 {len(selected_files)}개 파일에 대한 변환 테스트 시작...")

    all_results = []

    # Test each selected file
    for i, file_info in enumerate(selected_files, 1):
        print(f"\n📋 파일 {i}/{len(selected_files)} 테스트 중...")

        # Create file-specific output directory
        file_output_dir = os.path.join(output_dir, Path(file_info["name"]).stem)
        os.makedirs(file_output_dir, exist_ok=True)

        # Test the file
        result = test_single_file_conversion(
            file_info, api_key, base_url, file_output_dir
        )
        all_results.append(result)

        # Save individual results
        results_file = Path(file_output_dir) / "test_results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"   💾 결과 저장됨: {results_file}")

    # Generate summary report
    print(f"\n🎉 모든 파일 테스트 완료!")
    print("=" * 80)
    print("📊 전체 결과 요약:")
    print()

    for i, result in enumerate(all_results, 1):
        file_info = result["file_info"]
        marker_result = result["test_results"].get("marker")
        docling_result = result["test_results"].get("docling")

        print(f"{i}. {file_info['name']} ({file_info['size_mb']:.2f} MB)")

        if marker_result and docling_result:
            print(
                f"   🎯 Marker: {marker_result['conversion_time']:.2f}초, {marker_result['markdown_length']:,} 문자"
            )
            print(
                f"   🎯 Docling: {docling_result['conversion_time']:.2f}초, {docling_result['markdown_length']:,} 문자"
            )

            if marker_result["conversion_time"] < docling_result["conversion_time"]:
                speed_winner = "Marker"
                speed_ratio = (
                    docling_result["conversion_time"] / marker_result["conversion_time"]
                )
            else:
                speed_winner = "Docling"
                speed_ratio = (
                    marker_result["conversion_time"] / docling_result["conversion_time"]
                )

            print(f"   🏆 속도 우승자: {speed_winner} ({speed_ratio:.2f}배 빠름)")
        else:
            print("   ❌ 일부 테스트 실패")
        print()

    # Save summary results
    summary_file = Path(output_dir) / "summary_results.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

    print(f"💾 전체 결과가 저장되었습니다: {summary_file}")


if __name__ == "__main__":
    test_document_conversion_comparison()
