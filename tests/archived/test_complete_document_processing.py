#!/usr/bin/env python3
"""
전체 문서 파일을 사용한 완전한 청킹 및 임베딩 테스트
"""

import requests
import json
import os
import time
import math
from typing import List, Dict, Any
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 설정
BASE_URL = "http://localhost:8000"
API_KEY = "sk-kure-v1-test-key-12345"

# .env에서 청킹 설정 읽기
DEFAULT_CHUNK_STRATEGY = os.getenv("DEFAULT_CHUNK_STRATEGY", "recursive")
DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "380"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "70"))
DEFAULT_CHUNK_LANGUAGE = os.getenv("DEFAULT_CHUNK_LANGUAGE", "auto")

def load_complete_document() -> str:
    """전체 문서 파일을 로드합니다."""
    doc_path = "sample_docs/기업 문서 검색 도구 분석.md"
    
    if not os.path.exists(doc_path):
        raise FileNotFoundError(f"문서를 찾을 수 없습니다: {doc_path}")
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📄 전체 문서 로드 완료")
    print(f"   📏 총 문자 수: {len(content):,}")
    print(f"   📝 총 줄 수: {content.count(chr(10)) + 1:,}")
    print(f"   📊 단어 수 (추정): {len(content.split()):,}")
    
    return content

def test_complete_document_chunking(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """전체 문서를 .env 설정을 사용하여 청킹합니다."""
    print(f"\n🔪 전체 문서 청킹 테스트 (.env 설정 사용)")
    print("=" * 80)
    print(f"📋 .env 청킹 설정:")
    print(f"   전략: {DEFAULT_CHUNK_STRATEGY}")
    print(f"   청크 크기: {DEFAULT_CHUNK_SIZE}")
    print(f"   오버랩: {DEFAULT_CHUNK_OVERLAP}")
    print(f"   언어: {DEFAULT_CHUNK_LANGUAGE}")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # .env 설정을 기본으로 하고 비교를 위해 다른 전략들도 테스트
    strategies = [DEFAULT_CHUNK_STRATEGY, "sentence", "token"]
    # 중복 제거
    strategies = list(dict.fromkeys(strategies))
    all_chunks = {}

    for strategy in strategies:
        print(f"\n📋 전략: {strategy}")
        print("-" * 40)
        
        # .env 설정을 기본으로 사용하되, 전략만 변경
        payload = {
            "text": text,
            "strategy": strategy,
            "chunk_size": DEFAULT_CHUNK_SIZE,
            "overlap": DEFAULT_CHUNK_OVERLAP,
            "language": DEFAULT_CHUNK_LANGUAGE
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/v1/chunk", headers=headers, json=payload)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            chunks = result["data"]
            all_chunks[strategy] = chunks
            
            processing_time = end_time - start_time
            avg_chunk_size = result['total_tokens'] / len(chunks) if chunks else 0
            
            print(f"✅ 청킹 성공!")
            print(f"   ⏱️  처리 시간: {processing_time:.2f}초")
            print(f"   📊 총 청크 수: {len(chunks):,}")
            print(f"   🔢 총 토큰 수: {result['total_tokens']:,}")
            print(f"   📏 평균 청크 크기: {avg_chunk_size:.1f} 토큰")
            print(f"   📈 압축률: {result['original_length'] / result['total_tokens']:.2f} 문자/토큰")
            
            # 청크 크기 분포 분석
            token_counts = [chunk['token_count'] for chunk in chunks]
            min_tokens = min(token_counts)
            max_tokens = max(token_counts)
            
            print(f"   📉 토큰 범위: {min_tokens} ~ {max_tokens}")
            
            # 처음 3개와 마지막 3개 청크 미리보기
            print(f"\n   📝 청크 미리보기:")
            for i, chunk in enumerate(chunks[:3]):
                preview = chunk['text'][:80].replace('\n', ' ') + "..."
                print(f"      청크 {i+1}: {chunk['token_count']} 토큰 - {preview}")
            
            if len(chunks) > 6:
                print(f"      ... ({len(chunks)-6}개 청크 생략) ...")
                for i, chunk in enumerate(chunks[-3:], len(chunks)-2):
                    preview = chunk['text'][:80].replace('\n', ' ') + "..."
                    print(f"      청크 {i}: {chunk['token_count']} 토큰 - {preview}")
        else:
            print(f"❌ 청킹 실패: {response.status_code}")
            print(f"   오류: {response.text}")
    
    return all_chunks

def test_complete_embeddings(chunks: List[Dict[str, Any]], strategy_name: str, batch_size: int = 8) -> List[List[float]]:
    """전체 청크들의 임베딩을 배치로 생성합니다."""
    print(f"\n🧠 전체 임베딩 생성 테스트 ({strategy_name} 전략)")
    print("=" * 80)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    chunk_texts = [chunk['text'] for chunk in chunks]
    total_chunks = len(chunk_texts)
    total_batches = math.ceil(total_chunks / batch_size)
    
    print(f"📊 임베딩 처리 정보:")
    print(f"   📝 총 청크 수: {total_chunks:,}")
    print(f"   📦 배치 크기: {batch_size}")
    print(f"   🔄 총 배치 수: {total_batches:,}")
    
    all_embeddings = []
    total_tokens_used = 0
    total_processing_time = 0
    
    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, total_chunks)
        batch_texts = chunk_texts[start_idx:end_idx]
        
        print(f"\n🔄 배치 {batch_idx + 1}/{total_batches} 처리 중... ({len(batch_texts)}개 청크)")
        
        payload = {
            "input": batch_texts,
            "model": "nlpai-lab/KURE-v1"
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/embeddings", headers=headers, json=payload)
        end_time = time.time()
        
        batch_time = end_time - start_time
        total_processing_time += batch_time
        
        if response.status_code == 200:
            result = response.json()
            batch_embeddings = [data['embedding'] for data in result['data']]
            all_embeddings.extend(batch_embeddings)
            
            batch_tokens = result['usage']['total_tokens']
            total_tokens_used += batch_tokens
            
            print(f"   ✅ 성공: {len(batch_embeddings)}개 임베딩, {batch_tokens} 토큰, {batch_time:.2f}초")
        else:
            print(f"   ❌ 실패: {response.status_code} - {response.text}")
            return []
    
    if all_embeddings:
        embedding_dim = len(all_embeddings[0])
        avg_processing_time = total_processing_time / total_batches
        tokens_per_second = total_tokens_used / total_processing_time if total_processing_time > 0 else 0
        
        print(f"\n📈 임베딩 생성 완료!")
        print(f"   ✅ 총 임베딩 수: {len(all_embeddings):,}")
        print(f"   📏 임베딩 차원: {embedding_dim:,}")
        print(f"   ⏱️  총 처리 시간: {total_processing_time:.2f}초")
        print(f"   🚀 평균 배치 시간: {avg_processing_time:.2f}초")
        print(f"   🔢 총 토큰 사용량: {total_tokens_used:,}")
        print(f"   ⚡ 처리 속도: {tokens_per_second:.1f} 토큰/초")
        
        # 임베딩 통계
        print(f"\n📊 임베딩 통계 (처음 5개):")
        for i, embedding in enumerate(all_embeddings[:5]):
            avg_val = sum(embedding) / len(embedding)
            min_val = min(embedding)
            max_val = max(embedding)
            norm = math.sqrt(sum(x*x for x in embedding))
            print(f"   임베딩 {i+1}: 평균={avg_val:.4f}, 범위=[{min_val:.4f}, {max_val:.4f}], 노름={norm:.4f}")
    
    return all_embeddings

def test_similarity_analysis(chunks: List[Dict[str, Any]], embeddings: List[List[float]], strategy_name: str):
    """임베딩을 사용한 유사도 분석"""
    print(f"\n🔄 유사도 분석 ({strategy_name} 전략)")
    print("=" * 80)
    
    if len(chunks) < 2:
        print("❌ 유사도 분석을 위해서는 최소 2개의 청크가 필요합니다.")
        return
    
    # 처음 10개 청크로 유사도 행렬 계산
    sample_size = min(10, len(chunks))
    sample_chunks = chunks[:sample_size]
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    chunk_texts = [chunk['text'] for chunk in sample_chunks]
    
    payload = {
        "texts": chunk_texts,
        "model": "nlpai-lab/KURE-v1"
    }
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/similarity", headers=headers, json=payload)
    end_time = time.time()
    
    if response.status_code == 200:
        result = response.json()
        similarity_matrix = result['similarities']
        
        print(f"✅ 유사도 계산 성공!")
        print(f"   📊 분석 청크 수: {sample_size}")
        print(f"   ⏱️  처리 시간: {end_time - start_time:.2f}초")
        print(f"   🎯 사용 모델: {result['model']}")
        
        # 유사도 통계
        all_similarities = []
        for i in range(len(similarity_matrix)):
            for j in range(i+1, len(similarity_matrix[i])):
                all_similarities.append(similarity_matrix[i][j])
        
        if all_similarities:
            avg_sim = sum(all_similarities) / len(all_similarities)
            min_sim = min(all_similarities)
            max_sim = max(all_similarities)
            
            print(f"\n📈 유사도 통계:")
            print(f"   평균 유사도: {avg_sim:.4f}")
            print(f"   최소 유사도: {min_sim:.4f}")
            print(f"   최대 유사도: {max_sim:.4f}")
            
            # 가장 유사한 청크 쌍 찾기
            max_pair = (0, 0)
            max_similarity = 0
            for i in range(len(similarity_matrix)):
                for j in range(i+1, len(similarity_matrix[i])):
                    if similarity_matrix[i][j] > max_similarity:
                        max_similarity = similarity_matrix[i][j]
                        max_pair = (i, j)
            
            print(f"\n🏆 가장 유사한 청크 쌍:")
            print(f"   청크 {max_pair[0]+1} ↔ 청크 {max_pair[1]+1} (유사도: {max_similarity:.4f})")
            print(f"   청크 {max_pair[0]+1}: {sample_chunks[max_pair[0]]['text'][:100]}...")
            print(f"   청크 {max_pair[1]+1}: {sample_chunks[max_pair[1]]['text'][:100]}...")
    else:
        print(f"❌ 유사도 계산 실패: {response.status_code}")
        print(f"   오류: {response.text}")

def main():
    """메인 테스트 함수"""
    print("🧪 전체 문서를 사용한 완전한 청킹 및 임베딩 테스트")
    print("=" * 100)
    print(f"🔑 API 키: {API_KEY[:20]}...")
    print(f"🌐 기본 URL: {BASE_URL}")
    
    try:
        # 1. 전체 문서 로드
        document_text = load_complete_document()
        
        # 2. 전체 문서 청킹 (모든 전략)
        all_chunks = test_complete_document_chunking(document_text)
        
        # 3. .env 설정의 기본 전략으로 전체 임베딩 생성
        if DEFAULT_CHUNK_STRATEGY in all_chunks:
            chunks = all_chunks[DEFAULT_CHUNK_STRATEGY]
            embeddings = test_complete_embeddings(chunks, DEFAULT_CHUNK_STRATEGY)

            # 4. 유사도 분석
            if embeddings:
                test_similarity_analysis(chunks, embeddings, DEFAULT_CHUNK_STRATEGY)
        
        # 5. 전략별 성능 비교
        print(f"\n📊 전략별 청킹 성능 비교")
        print("=" * 80)
        print(f"{'전략':<12} {'청크수':<8} {'평균토큰':<10} {'효율성':<10}")
        print("-" * 50)
        
        for strategy, chunks in all_chunks.items():
            if chunks:
                total_tokens = sum(chunk['token_count'] for chunk in chunks)
                avg_tokens = total_tokens / len(chunks)
                efficiency = len(document_text) / total_tokens  # 문자/토큰 비율
                print(f"{strategy:<12} {len(chunks):<8} {avg_tokens:<10.1f} {efficiency:<10.2f}")
        
        print(f"\n🎉 전체 문서 처리 테스트 완료!")
        
    except FileNotFoundError as e:
        print(f"❌ 파일 오류: {e}")
    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
