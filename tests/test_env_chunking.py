#!/usr/bin/env python3
"""
.env 설정을 사용한 전체 문서 청킹 및 임베딩 테스트
"""

import requests
import json
import os
import time
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

def main():
    print("🧪 .env 설정을 사용한 전체 문서 테스트")
    print("=" * 60)
    print(f"📋 .env 청킹 설정:")
    print(f"   전략: {DEFAULT_CHUNK_STRATEGY}")
    print(f"   청크 크기: {DEFAULT_CHUNK_SIZE}")
    print(f"   오버랩: {DEFAULT_CHUNK_OVERLAP}")
    print(f"   언어: {DEFAULT_CHUNK_LANGUAGE}")
    
    # 1. 전체 문서 로드
    doc_path = "sample_docs/기업 문서 검색 도구 분석.md"
    
    if not os.path.exists(doc_path):
        print(f"❌ 문서를 찾을 수 없습니다: {doc_path}")
        return
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n📄 전체 문서 로드:")
    print(f"   📏 총 문자 수: {len(content):,}")
    print(f"   📝 총 줄 수: {content.count(chr(10)) + 1:,}")
    print(f"   📊 단어 수 (추정): {len(content.split()):,}")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 2. .env 설정으로 전체 문서 청킹
    print(f"\n🔪 전체 문서 청킹 (.env 설정 사용)...")
    
    chunk_payload = {
        "text": content,
        "strategy": DEFAULT_CHUNK_STRATEGY,
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "overlap": DEFAULT_CHUNK_OVERLAP,
        "language": DEFAULT_CHUNK_LANGUAGE
    }
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/v1/chunk", headers=headers, json=chunk_payload)
    chunk_time = time.time() - start_time
    
    if response.status_code == 200:
        chunk_result = response.json()
        chunks = chunk_result["data"]
        
        print(f"✅ 청킹 성공!")
        print(f"   ⏱️  처리 시간: {chunk_time:.2f}초")
        print(f"   📊 총 청크 수: {len(chunks):,}")
        print(f"   🔢 총 토큰 수: {chunk_result['total_tokens']:,}")
        print(f"   📏 평균 청크 크기: {chunk_result['total_tokens'] / len(chunks):.1f} 토큰")
        print(f"   📈 압축률: {chunk_result['original_length'] / chunk_result['total_tokens']:.2f} 문자/토큰")
        
        # 청크 크기 분포
        token_counts = [chunk['token_count'] for chunk in chunks]
        min_tokens = min(token_counts)
        max_tokens = max(token_counts)
        print(f"   📉 토큰 범위: {min_tokens} ~ {max_tokens}")
        
        # 처음 3개 청크 미리보기
        print(f"\n📝 청크 미리보기 (처음 3개):")
        for i, chunk in enumerate(chunks[:3]):
            preview = chunk['text'][:100].replace('\n', ' ') + "..."
            print(f"   청크 {i+1}: {chunk['token_count']} 토큰")
            print(f"      {preview}")
        
        # 3. 전체 청크 임베딩 (배치 처리)
        print(f"\n🧠 전체 청크 임베딩 생성...")
        
        batch_size = 5  # 작은 배치로 시작
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        print(f"   📊 임베딩 처리 정보:")
        print(f"      총 청크 수: {len(chunks):,}")
        print(f"      배치 크기: {batch_size}")
        print(f"      총 배치 수: {total_batches:,}")
        
        all_embeddings = []
        total_tokens_used = 0
        total_embed_time = 0
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(chunks))
            batch_chunks = chunks[start_idx:end_idx]
            batch_texts = [chunk['text'] for chunk in batch_chunks]
            
            print(f"\n   🔄 배치 {batch_idx + 1}/{total_batches} 처리 중... ({len(batch_texts)}개 청크)")
            
            embed_payload = {
                "input": batch_texts,
                "model": "nlpai-lab/KURE-v1"
            }
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/embeddings", headers=headers, json=embed_payload)
            batch_time = time.time() - start_time
            total_embed_time += batch_time
            
            if response.status_code == 200:
                embed_result = response.json()
                batch_embeddings = [data['embedding'] for data in embed_result['data']]
                all_embeddings.extend(batch_embeddings)
                
                batch_tokens = embed_result['usage']['total_tokens']
                total_tokens_used += batch_tokens
                
                print(f"      ✅ 성공: {len(batch_embeddings)}개 임베딩, {batch_tokens} 토큰, {batch_time:.2f}초")
            else:
                print(f"      ❌ 실패: {response.status_code} - {response.text}")
                break
        
        if all_embeddings:
            embedding_dim = len(all_embeddings[0])
            tokens_per_second = total_tokens_used / total_embed_time if total_embed_time > 0 else 0
            
            print(f"\n📈 임베딩 생성 완료!")
            print(f"   ✅ 총 임베딩 수: {len(all_embeddings):,}")
            print(f"   📏 임베딩 차원: {embedding_dim:,}")
            print(f"   ⏱️  총 처리 시간: {total_embed_time:.2f}초")
            print(f"   🔢 총 토큰 사용량: {total_tokens_used:,}")
            print(f"   ⚡ 처리 속도: {tokens_per_second:.1f} 토큰/초")
            
            # 4. 유사도 분석 (처음 5개 청크)
            print(f"\n🔄 유사도 분석 (처음 5개 청크)...")
            
            sample_texts = [chunk['text'] for chunk in chunks[:5]]
            
            sim_payload = {
                "texts": sample_texts,
                "model": "nlpai-lab/KURE-v1"
            }
            
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/similarity", headers=headers, json=sim_payload)
            sim_time = time.time() - start_time
            
            if response.status_code == 200:
                sim_result = response.json()
                similarities = sim_result['similarities']
                
                print(f"✅ 유사도 계산 성공!")
                print(f"   ⏱️  처리 시간: {sim_time:.2f}초")
                print(f"   📊 행렬 크기: {len(similarities)}x{len(similarities[0])}")
                
                # 유사도 행렬 출력
                print(f"\n📈 유사도 행렬:")
                print("     ", end="")
                for i in range(len(similarities)):
                    print(f"청크{i+1:2d}", end="  ")
                print()
                
                for i, row in enumerate(similarities):
                    print(f"청크{i+1:2d}", end="  ")
                    for val in row:
                        print(f"{val:.3f}", end="  ")
                    print()
                
                # 가장 유사한 청크 쌍
                max_similarity = 0
                max_pair = (0, 0)
                for i in range(len(similarities)):
                    for j in range(i+1, len(similarities[i])):
                        if similarities[i][j] > max_similarity:
                            max_similarity = similarities[i][j]
                            max_pair = (i, j)
                
                print(f"\n🏆 가장 유사한 청크 쌍:")
                print(f"   청크 {max_pair[0]+1} ↔ 청크 {max_pair[1]+1} (유사도: {max_similarity:.4f})")
            else:
                print(f"❌ 유사도 계산 실패: {response.status_code}")
        
        # 5. 전체 처리 요약
        total_time = chunk_time + total_embed_time
        print(f"\n📊 전체 처리 요약:")
        print(f"   📄 문서 크기: {len(content):,} 문자")
        print(f"   🔪 청킹 시간: {chunk_time:.2f}초")
        print(f"   🧠 임베딩 시간: {total_embed_time:.2f}초")
        print(f"   ⏱️  총 처리 시간: {total_time:.2f}초")
        print(f"   📊 청크 수: {len(chunks):,}")
        print(f"   🔢 토큰 사용량: {total_tokens_used:,}")
        print(f"   ⚡ 전체 처리 속도: {len(content) / total_time:.1f} 문자/초")
        
        print(f"\n🎉 .env 설정 기반 전체 문서 테스트 완료!")
        
    else:
        print(f"❌ 청킹 실패: {response.status_code}")
        print(f"   오류: {response.text}")

if __name__ == "__main__":
    main()
