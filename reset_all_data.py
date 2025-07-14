#!/usr/bin/env python3
"""
전체 데이터 초기화 스크립트
- Qdrant 컬렉션 삭제 및 재생성
- MeiliSearch 인덱스 삭제 및 재생성
- 로컬 스토리지 파일 삭제
- 데이터베이스 초기화 (필요시)
"""

import os
import shutil
import asyncio
import httpx
import meilisearch
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

class DataResetManager:
    def __init__(self):
        # Qdrant 설정
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.qdrant_collection = "ragnaforge_documents"
        
        # MeiliSearch 설정
        self.meilisearch_url = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
        self.meilisearch_api_key = os.getenv("MEILISEARCH_API_KEY")
        self.meilisearch_index = "ragnaforge_documents"
        
        # 스토리지 설정
        self.storage_base_path = os.getenv("STORAGE_BASE_PATH", "./data/storage")
        self.upload_dir = os.path.join(self.storage_base_path, os.getenv("UPLOAD_DIR", "uploads"))
        self.processed_dir = os.path.join(self.storage_base_path, os.getenv("PROCESSED_DIR", "processed"))
        self.temp_dir = os.path.join(self.storage_base_path, os.getenv("TEMP_DIR", "temp"))
        
        # 추가 정리할 디렉토리들
        self.additional_dirs = [
            "./models",  # 캐시된 모델 파일들
            "./data",    # 전체 데이터 디렉토리
            "./__pycache__",  # Python 캐시
        ]

    def reset_qdrant(self):
        """Qdrant 컬렉션 초기화"""
        try:
            logger.info("🔄 Qdrant 초기화 시작...")
            
            # Qdrant 클라이언트 생성 (SSL 검증 비활성화)
            if self.qdrant_api_key:
                client = QdrantClient(
                    host=self.qdrant_host,
                    port=self.qdrant_port,
                    api_key=self.qdrant_api_key,
                    https=True,
                    verify=False  # SSL 인증서 검증 비활성화
                )
            else:
                client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
            
            # 기존 컬렉션 삭제
            try:
                collections = client.get_collections().collections
                collection_names = [col.name for col in collections]
                
                if self.qdrant_collection in collection_names:
                    logger.info(f"📦 기존 컬렉션 '{self.qdrant_collection}' 삭제 중...")
                    client.delete_collection(self.qdrant_collection)
                    logger.info("✅ 컬렉션 삭제 완료")
                else:
                    logger.info(f"📦 컬렉션 '{self.qdrant_collection}'이 존재하지 않음")
                    
            except Exception as e:
                logger.warning(f"컬렉션 삭제 중 오류 (무시): {str(e)}")
            
            # 새 컬렉션 생성
            logger.info(f"📦 새 컬렉션 '{self.qdrant_collection}' 생성 중...")
            client.create_collection(
                collection_name=self.qdrant_collection,
                vectors_config=VectorParams(
                    size=768,  # KURE-v1 모델의 벡터 차원
                    distance=Distance.COSINE
                )
            )
            logger.info("✅ Qdrant 초기화 완료")
            
        except Exception as e:
            logger.error(f"❌ Qdrant 초기화 실패: {str(e)}")
            raise

    def reset_meilisearch(self):
        """MeiliSearch 인덱스 초기화"""
        try:
            logger.info("🔍 MeiliSearch 초기화 시작...")
            
            # MeiliSearch 클라이언트 생성
            client = meilisearch.Client(
                url=self.meilisearch_url,
                api_key=self.meilisearch_api_key
            )
            
            # 기존 인덱스 삭제
            try:
                indexes = client.get_indexes()
                index_names = [idx.uid for idx in indexes['results']]
                
                if self.meilisearch_index in index_names:
                    logger.info(f"📑 기존 인덱스 '{self.meilisearch_index}' 삭제 중...")
                    client.delete_index(self.meilisearch_index)
                    logger.info("✅ 인덱스 삭제 완료")
                else:
                    logger.info(f"📑 인덱스 '{self.meilisearch_index}'이 존재하지 않음")
                    
            except Exception as e:
                logger.warning(f"인덱스 삭제 중 오류 (무시): {str(e)}")
            
            # 새 인덱스 생성
            logger.info(f"📑 새 인덱스 '{self.meilisearch_index}' 생성 중...")
            client.create_index(self.meilisearch_index, {'primaryKey': 'id'})
            
            # 인덱스 설정 구성
            index = client.index(self.meilisearch_index)
            
            # 검색 가능한 속성 설정
            index.update_searchable_attributes([
                "title", "content", "file_name", "file_type", "metadata"
            ])
            
            # 필터링 가능한 속성 설정
            index.update_filterable_attributes([
                "document_id", "file_type", "file_name", "created_at", "chunk_index", "file_size"
            ])
            
            # 정렬 가능한 속성 설정
            index.update_sortable_attributes([
                "created_at", "file_size", "chunk_index"
            ])
            
            logger.info("✅ MeiliSearch 초기화 완료")
            
        except Exception as e:
            logger.error(f"❌ MeiliSearch 초기화 실패: {str(e)}")
            raise

    def reset_local_storage(self):
        """로컬 스토리지 초기화"""
        try:
            logger.info("💾 로컬 스토리지 초기화 시작...")
            
            # 스토리지 디렉토리들 삭제
            storage_dirs = [self.upload_dir, self.processed_dir, self.temp_dir]
            
            for dir_path in storage_dirs:
                if os.path.exists(dir_path):
                    logger.info(f"📁 디렉토리 삭제: {dir_path}")
                    shutil.rmtree(dir_path)
                else:
                    logger.info(f"📁 디렉토리가 존재하지 않음: {dir_path}")
            
            # 추가 디렉토리들 삭제
            for dir_path in self.additional_dirs:
                if os.path.exists(dir_path):
                    logger.info(f"📁 추가 디렉토리 삭제: {dir_path}")
                    shutil.rmtree(dir_path)
            
            # 스토리지 디렉토리 재생성
            for dir_path in storage_dirs:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"📁 디렉토리 재생성: {dir_path}")
            
            logger.info("✅ 로컬 스토리지 초기화 완료")
            
        except Exception as e:
            logger.error(f"❌ 로컬 스토리지 초기화 실패: {str(e)}")
            raise

    def reset_cache_files(self):
        """캐시 파일들 정리"""
        try:
            logger.info("🧹 캐시 파일 정리 시작...")
            
            # Python 캐시 파일들 정리
            cache_patterns = [
                "**/__pycache__",
                "**/*.pyc",
                "**/*.pyo",
                "**/.pytest_cache",
            ]
            
            import glob
            for pattern in cache_patterns:
                files = glob.glob(pattern, recursive=True)
                for file_path in files:
                    try:
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                        else:
                            os.remove(file_path)
                        logger.info(f"🗑️ 캐시 삭제: {file_path}")
                    except Exception as e:
                        logger.warning(f"캐시 삭제 실패 (무시): {file_path} - {str(e)}")
            
            logger.info("✅ 캐시 파일 정리 완료")
            
        except Exception as e:
            logger.error(f"❌ 캐시 파일 정리 실패: {str(e)}")

    def verify_reset(self):
        """초기화 결과 확인"""
        try:
            logger.info("🔍 초기화 결과 확인 중...")
            
            # Qdrant 확인
            try:
                if self.qdrant_api_key:
                    client = QdrantClient(
                        host=self.qdrant_host,
                        port=self.qdrant_port,
                        api_key=self.qdrant_api_key,
                        https=True,
                        verify=False  # SSL 인증서 검증 비활성화
                    )
                else:
                    client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
                
                collection_info = client.get_collection(self.qdrant_collection)
                logger.info(f"✅ Qdrant 컬렉션 확인: {collection_info.points_count}개 포인트")
                
            except Exception as e:
                logger.warning(f"Qdrant 확인 실패: {str(e)}")
            
            # MeiliSearch 확인
            try:
                client = meilisearch.Client(
                    url=self.meilisearch_url,
                    api_key=self.meilisearch_api_key
                )
                index = client.index(self.meilisearch_index)
                stats = index.get_stats()
                logger.info(f"✅ MeiliSearch 인덱스 확인: {stats.get('numberOfDocuments', 0)}개 문서")
                
            except Exception as e:
                logger.warning(f"MeiliSearch 확인 실패: {str(e)}")
            
            # 스토리지 확인
            for dir_path in [self.upload_dir, self.processed_dir, self.temp_dir]:
                if os.path.exists(dir_path):
                    file_count = len(os.listdir(dir_path))
                    logger.info(f"✅ 스토리지 디렉토리 확인: {dir_path} ({file_count}개 파일)")
                else:
                    logger.warning(f"❌ 스토리지 디렉토리 없음: {dir_path}")
            
        except Exception as e:
            logger.error(f"❌ 초기화 결과 확인 실패: {str(e)}")

    def reset_all(self):
        """전체 데이터 초기화 실행"""
        logger.info("🚀 전체 데이터 초기화 시작...")
        logger.info("=" * 50)
        
        try:
            # 1. Qdrant 초기화
            self.reset_qdrant()
            
            # 2. MeiliSearch 초기화
            self.reset_meilisearch()
            
            # 3. 로컬 스토리지 초기화
            self.reset_local_storage()
            
            # 4. 캐시 파일 정리
            self.reset_cache_files()
            
            # 5. 결과 확인
            self.verify_reset()
            
            logger.info("=" * 50)
            logger.info("🎉 전체 데이터 초기화 완료!")
            logger.info("이제 새로운 문서를 업로드할 수 있습니다.")
            
        except Exception as e:
            logger.error(f"❌ 전체 데이터 초기화 실패: {str(e)}")
            raise

def main():
    """메인 함수"""
    print("⚠️  경고: 이 스크립트는 모든 데이터를 삭제합니다!")
    print("- Qdrant 컬렉션")
    print("- MeiliSearch 인덱스")
    print("- 로컬 스토리지 파일")
    print("- 캐시 파일")
    print()
    
    # 사용자 확인
    confirm = input("정말로 모든 데이터를 초기화하시겠습니까? (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("❌ 초기화가 취소되었습니다.")
        return
    
    # 추가 확인
    confirm2 = input("다시 한 번 확인합니다. 모든 데이터가 삭제됩니다. 계속하시겠습니까? (YES): ").strip()
    
    if confirm2 != 'YES':
        print("❌ 초기화가 취소되었습니다.")
        return
    
    # 초기화 실행
    try:
        reset_manager = DataResetManager()
        reset_manager.reset_all()
        
    except Exception as e:
        logger.error(f"초기화 중 오류 발생: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
