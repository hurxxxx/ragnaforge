# 문서 변환 기능 가이드

## 개요

KURE Embed API에 datalab-marker를 사용한 문서 변환 기능이 추가되었습니다. 이 기능을 통해 다양한 형식의 문서를 마크다운, JSON, HTML로 변환할 수 있습니다.

## 지원 형식

### 입력 형식
- **PDF**: Adobe PDF 문서
- **DOCX**: Microsoft Word 문서  
- **PPTX**: Microsoft PowerPoint 프레젠테이션
- **HTML**: 웹 페이지 문서
- **EPUB**: 전자책 형식
- **이미지**: PNG, JPG, JPEG, TIFF, BMP

### 출력 형식
- **Markdown**: 구조화된 텍스트 형식
- **JSON**: 구조화된 데이터 형식 (블록 단위)
- **HTML**: 웹 페이지 형식

## API 사용법

### 엔드포인트
```
POST /v1/convert
```

### 요청 파라미터
- `file` (required): 변환할 문서 파일
- `output_format` (optional): 출력 형식 (markdown, json, html) - 기본값: markdown
- `extract_images` (optional): 이미지 추출 여부 - 기본값: true
- `use_llm` (optional): LLM 향상 기능 사용 여부 - 기본값: false

### 응답 형식
```json
{
  "object": "document_conversion",
  "markdown_content": "변환된 마크다운 내용...",
  "json_content": null,
  "html_content": null,
  "images": ["image1.png", "image2.png"],
  "metadata": {"raw_metadata": "..."},
  "output_format": "markdown",
  "file_path": "/path/to/output/file.md"
}
```

## 사용 예제

### cURL 예제
```bash
# PDF를 마크다운으로 변환
curl -X POST http://localhost:8000/v1/convert \
  -F 'file=@document.pdf' \
  -F 'output_format=markdown' \
  -F 'extract_images=true'

# DOCX를 JSON으로 변환
curl -X POST http://localhost:8000/v1/convert \
  -F 'file=@document.docx' \
  -F 'output_format=json' \
  -F 'extract_images=false'
```

### Python 예제
```python
import requests

# 파일 변환
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    data = {
        'output_format': 'markdown',
        'extract_images': True,
        'use_llm': False
    }
    
    response = requests.post(
        'http://localhost:8000/v1/convert',
        files=files,
        data=data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"변환 완료: {result['file_path']}")
        print(f"마크다운 길이: {len(result['markdown_content'])} 문자")
        print(f"추출된 이미지: {len(result['images'])}개")
    else:
        print(f"변환 실패: {response.status_code}")
```

## 출력 파일 구조

변환된 파일들은 다음과 같은 구조로 저장됩니다:

```
converted_docs/
├── markdown/          # 마크다운 파일들
│   ├── document1.md
│   └── document2.md
├── json/              # JSON 파일들
│   ├── document1.json
│   └── document2.json
├── html/              # HTML 파일들
│   ├── document1.html
│   └── document2.html
└── images/            # 추출된 이미지들
    ├── document1_image_1.png
    ├── document1_image_2.png
    └── document2_image_1.png
```

## 고급 기능

### LLM 향상 기능
`use_llm=true` 옵션을 사용하면 LLM을 활용하여 변환 품질을 향상시킬 수 있습니다:
- 테이블 병합 및 포맷팅 개선
- 인라인 수식 처리 향상
- 폼 데이터 추출 개선

**주의**: LLM 기능을 사용하려면 적절한 API 키 설정이 필요합니다.

### 이미지 추출
`extract_images=true` 옵션을 사용하면:
- 문서 내 모든 이미지가 PNG 형식으로 추출됩니다
- 이미지는 `images/` 디렉토리에 저장됩니다
- 마크다운에서는 이미지 링크가 자동으로 생성됩니다

## 테스트

### 기본 테스트
```bash
# 기본 기능 테스트
PYTHONPATH=. python -m pytest tests/test_simple_document_conversion.py -v

# 실제 파일 테스트 (sample_docs/ 파일 사용)
PYTHONPATH=. python -m pytest tests/test_real_document_conversion.py -v -s

# API 테스트 (서버 실행 필요)
PYTHONPATH=. python -m pytest tests/test_real_api_conversion.py -v -s
```

### 수동 테스트
```bash
# 서비스 테스트
PYTHONPATH=. python tests/test_real_document_conversion.py

# API 테스트 (서버 실행 필요)
PYTHONPATH=. python tests/test_real_api_conversion.py
```

## 성능 고려사항

- **변환 시간**: 문서 크기와 복잡도에 따라 수초에서 수분까지 소요될 수 있습니다
- **메모리 사용량**: 대용량 문서 처리 시 충분한 메모리가 필요합니다
- **GPU 가속**: CUDA가 사용 가능한 환경에서 더 빠른 처리가 가능합니다
- **LLM 사용**: LLM 기능 사용 시 추가 시간이 소요되지만 품질이 향상됩니다

## 문제 해결

### 일반적인 오류

1. **지원하지 않는 파일 형식**
   ```
   HTTP 400: Unsupported file format
   ```
   → 지원되는 형식인지 확인하세요

2. **파일 크기 제한**
   ```
   HTTP 413: Request Entity Too Large
   ```
   → 파일 크기를 줄이거나 서버 설정을 조정하세요

3. **변환 시간 초과**
   ```
   HTTP 504: Gateway Timeout
   ```
   → 더 작은 문서로 나누어 처리하거나 타임아웃 설정을 늘리세요

### 로그 확인
서버 로그에서 상세한 오류 정보를 확인할 수 있습니다:
```bash
python main.py
# 또는 로그 레벨 조정
LOG_LEVEL=DEBUG python main.py
```

## 의존성

이 기능을 사용하려면 다음 패키지가 설치되어야 합니다:
```bash
pip install marker-pdf[full]
```

marker-pdf[full]에는 다음이 포함됩니다:
- 기본 PDF 처리 기능
- DOCX, PPTX 지원
- 이미지 처리 기능
- OCR 기능
- 테이블 인식 기능
