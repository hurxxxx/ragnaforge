#!/usr/bin/env python3
"""
.env 설정을 사용한 부분 문서 청킹 및 임베딩 테스트 (안정성을 위해)
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
    print("🧪 .env 설정을 사용한 실제 문서 테스트 (부분 처리)")
    print("=" * 70)
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
        full_content = f.read()
    
    # 안정성을 위해 문서의 처음 10,000자만 사용
    content = full_content[:10000]
    
    print(f"\n📄 문서 로드:")
    print(f"   📏 전체 문서: {len(full_content):,} 문자")
    print(f"   📝 테스트 부분: {len(content):,} 문자 (처음 10,000자)")
    print(f"   📊 테스트 단어 수: {len(content.split()):,}")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 2. .env 설정으로 청킹
    print(f"\n🔪 문서 청킹 (.env 설정 사용)...")
    
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
        
        # 모든 청크 미리보기
        print(f"\n📝 모든 청크 미리보기:")
        for i, chunk in enumerate(chunks):
            preview = chunk['text'][:80].replace('\n', ' ') + "..."
            print(f"   청크 {i+1}: {chunk['token_count']} 토큰")
            print(f"      {preview}")
        
        # 3. 모든 청크 임베딩
        print(f"\n🧠 모든 청크 임베딩 생성...")
        
        chunk_texts = [chunk['text'] for chunk in chunks]
        
        embed_payload = {
            "input": chunk_texts,
            "model": "nlpai-lab/KURE-v1"
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/embeddings", headers=headers, json=embed_payload)
        embed_time = time.time() - start_time
        
        if response.status_code == 200:
            embed_result = response.json()
            embeddings = [data['embedding'] for data in embed_result['data']]
            
            embedding_dim = len(embeddings[0])
            total_tokens_used = embed_result['usage']['total_tokens']
            tokens_per_second = total_tokens_used / embed_time if embed_time > 0 else 0
            
            print(f"✅ 임베딩 생성 성공!")
            print(f"   ✅ 총 임베딩 수: {len(embeddings):,}")
            print(f"   📏 임베딩 차원: {embedding_dim:,}")
            print(f"   ⏱️  처리 시간: {embed_time:.2f}초")
            print(f"   🔢 토큰 사용량: {total_tokens_used:,}")
            print(f"   ⚡ 처리 속도: {tokens_per_second:.1f} 토큰/초")
            
            # 임베딩 통계
            print(f"\n📊 임베딩 통계:")
            for i, embedding in enumerate(embeddings):
                avg_val = sum(embedding) / len(embedding)
                min_val = min(embedding)
                max_val = max(embedding)
                norm = (sum(x*x for x in embedding)) ** 0.5
                print(f"   임베딩 {i+1}: 평균={avg_val:.4f}, 범위=[{min_val:.4f}, {max_val:.4f}], 노름={norm:.4f}")
            
            # 4. 유사도 분석
            print(f"\n🔄 유사도 분석...")
            
            sim_payload = {
                "texts": chunk_texts,
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
                
                # 유사도 통계
                all_similarities = []
                for i in range(len(similarities)):
                    for j in range(i+1, len(similarities[i])):
                        all_similarities.append(similarities[i][j])
                
                if all_similarities:
                    avg_sim = sum(all_similarities) / len(all_similarities)
                    min_sim = min(all_similarities)
                    max_sim = max(all_similarities)
                    
                    print(f"\n📈 유사도 통계:")
                    print(f"   평균 유사도: {avg_sim:.4f}")
                    print(f"   최소 유사도: {min_sim:.4f}")
                    print(f"   최대 유사도: {max_sim:.4f}")
                    
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
                    print(f"   청크 {max_pair[0]+1}: {chunks[max_pair[0]]['text'][:100]}...")
                    print(f"   청크 {max_pair[1]+1}: {chunks[max_pair[1]]['text'][:100]}...")
            else:
                print(f"❌ 유사도 계산 실패: {response.status_code}")
                print(f"   오류: {response.text}")
        else:
            print(f"❌ 임베딩 실패: {response.status_code}")
            print(f"   오류: {response.text}")
        
        # 5. 전체 처리 요약
        total_time = chunk_time + embed_time
        print(f"\n📊 전체 처리 요약:")
        print(f"   📄 처리된 문서 크기: {len(content):,} 문자")
        print(f"   🔪 청킹 시간: {chunk_time:.2f}초")
        print(f"   🧠 임베딩 시간: {embed_time:.2f}초")
        print(f"   ⏱️  총 처리 시간: {total_time:.2f}초")
        print(f"   📊 생성된 청크 수: {len(chunks):,}")
        print(f"   🔢 사용된 토큰: {total_tokens_used:,}")
        print(f"   ⚡ 전체 처리 속도: {len(content) / total_time:.1f} 문자/초")
        print(f"   🎯 .env 설정 적용: ✅")
        
        print(f"\n🎉 .env 설정 기반 실제 문서 테스트 완료!")
        
    else:
        print(f"❌ 청킹 실패: {response.status_code}")
        print(f"   오류: {response.text}")

if __name__ == "__main__":
    main()
