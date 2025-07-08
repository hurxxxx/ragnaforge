#!/usr/bin/env python3
"""
복잡한 문장을 사용한 임베딩 모델 간 유사도 검증 테스트

이 테스트는 다양한 복잡성과 의미적 뉘앙스를 가진 문장들을 사용하여
임베딩 모델들의 성능을 비교합니다.
"""

import asyncio
import json
import logging
import numpy as np
import time
from typing import Dict, List, Tuple, Any
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import pearsonr, spearmanr

from services.embedding_service import embedding_service
from config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplexEmbeddingSimilarityTest:
    """복잡한 문장을 사용한 임베딩 유사도 테스트 클래스"""
    
    def __init__(self):
        self.models = [
            "dragonkue/snowflake-arctic-embed-l-v2.0-ko",
            "nlpai-lab/KURE-v1"
        ]
        
        # 복잡한 테스트 문장들 정의
        self.test_scenarios = self._define_test_scenarios()
        
    def _define_test_scenarios(self) -> Dict[str, List[Tuple[str, str, float]]]:
        """복잡한 테스트 시나리오들을 정의합니다."""
        
        scenarios = {
            "기술_문서_유사성": [
                (
                    "인공지능 기반의 자연어 처리 시스템은 대규모 언어 모델을 활용하여 텍스트의 의미를 이해하고 생성할 수 있는 능력을 갖추고 있다.",
                    "딥러닝을 이용한 NLP 기술은 트랜스포머 아키텍처를 통해 문맥을 파악하고 언어를 생성하는 기능을 제공한다.",
                    0.8  # 높은 유사도 기대
                ),
                (
                    "벡터 데이터베이스는 고차원 벡터 공간에서 유사도 검색을 효율적으로 수행할 수 있도록 설계된 특수한 데이터베이스 시스템이다.",
                    "임베딩 저장소는 다차원 벡터들을 인덱싱하여 빠른 근사 최근접 이웃 검색을 가능하게 하는 데이터 관리 솔루션이다.",
                    0.75  # 높은 유사도 기대
                ),
                (
                    "RAG(Retrieval-Augmented Generation) 시스템은 외부 지식 베이스에서 관련 정보를 검색하여 생성 모델의 응답 품질을 향상시키는 하이브리드 접근법이다.",
                    "검색 증강 생성 모델은 문서 저장소에서 컨텍스트를 가져와 더 정확하고 사실적인 텍스트를 생성하는 AI 기술이다.",
                    0.85  # 매우 높은 유사도 기대
                )
            ],
            
            "비즈니스_문맥_이해": [
                (
                    "우리 회사의 분기별 매출 성장률이 전년 동기 대비 15% 증가했으며, 이는 주로 신제품 출시와 마케팅 전략의 성공에 기인한다.",
                    "이번 분기 수익이 작년 같은 기간보다 15% 늘어났는데, 새로운 상품 런칭과 효과적인 광고 캠페인이 주요 원인으로 분석된다.",
                    0.8
                ),
                (
                    "고객 만족도 조사 결과, 서비스 품질에 대한 평가는 긍정적이었으나 배송 시간과 관련된 불만이 지속적으로 제기되고 있다.",
                    "소비자 설문조사에서 제품 퀄리티는 좋은 평가를 받았지만, 배송 지연 문제에 대한 개선 요구가 계속 나오고 있다.",
                    0.75
                ),
                (
                    "디지털 트랜스포메이션 프로젝트의 일환으로 클라우드 마이그레이션을 추진하여 운영 효율성을 높이고 비용을 절감할 계획이다.",
                    "회사의 디지털 혁신 계획에 따라 시스템을 클라우드로 이전하여 업무 효율을 개선하고 운영비를 줄이려고 한다.",
                    0.82
                )
            ],
            
            "학술_논문_스타일": [
                (
                    "본 연구에서는 심층 신경망을 이용한 다중 모달 감정 분석 모델을 제안하며, 텍스트와 이미지 정보를 융합하여 감정 인식 정확도를 향상시키는 방법론을 제시한다.",
                    "이 논문은 딥러닝 기반의 멀티모달 감정 분류 시스템을 개발하였으며, 언어적 특징과 시각적 특징을 결합하여 감정 판별 성능을 개선하는 접근법을 소개한다.",
                    0.85
                ),
                (
                    "실험 결과, 제안된 알고리즘은 기존 베이스라인 모델 대비 F1-score에서 12.3% 향상된 성능을 보였으며, 특히 부정적 감정 분류에서 뛰어난 성과를 나타냈다.",
                    "성능 평가에서 우리가 개발한 방법은 기준 모델보다 F1 점수가 12.3% 높았고, 특히 네거티브 감정을 구분하는 데 우수한 결과를 보여주었다.",
                    0.8
                )
            ],
            
            "일상_대화_vs_전문용어": [
                (
                    "오늘 날씨가 정말 좋네요. 산책하기 딱 좋은 것 같아요.",
                    "기상 조건이 매우 양호하여 야외 활동에 적합한 환경이 조성되었습니다.",
                    0.6  # 중간 정도 유사도
                ),
                (
                    "컴퓨터가 갑자기 느려져서 작업하기 힘들어요.",
                    "시스템 성능 저하로 인해 업무 효율성이 현저히 감소하고 있습니다.",
                    0.7
                ),
                (
                    "이 음식 정말 맛있다! 또 먹고 싶어.",
                    "본 요리의 풍미가 탁월하여 재섭취 의향이 높습니다.",
                    0.65
                )
            ],
            
            "부정_문장_vs_긍정_문장": [
                (
                    "이 제품은 품질이 매우 우수하고 사용하기 편리하여 강력히 추천합니다.",
                    "이 상품은 품질이 형편없고 사용하기 불편해서 절대 추천하지 않습니다.",
                    0.3  # 낮은 유사도 기대 (반대 의미)
                ),
                (
                    "프로젝트가 예정보다 빨리 완료되어 모든 팀원들이 만족하고 있습니다.",
                    "프로젝트가 계획보다 지연되어 팀원들이 모두 불만을 표하고 있습니다.",
                    0.25
                ),
                (
                    "새로운 정책이 도입되어 업무 효율성이 크게 향상되었습니다.",
                    "새로운 규정 때문에 업무 처리가 더욱 복잡해지고 비효율적이 되었습니다.",
                    0.2
                )
            ],
            
            "문맥_의존적_의미": [
                (
                    "은행에서 돈을 인출했습니다.",
                    "강가에서 낚시를 했습니다.",
                    0.1  # 매우 낮은 유사도 (동음이의어)
                ),
                (
                    "사과를 먹었습니다.",
                    "실수에 대해 사과했습니다.",
                    0.15
                ),
                (
                    "배가 항구에 정박했습니다.",
                    "배가 고파서 음식을 먹었습니다.",
                    0.1
                )
            ]
        }
        
        return scenarios
    
    def calculate_embedding_similarity(self, text1: str, text2: str, model: str) -> float:
        """두 텍스트 간의 임베딩 유사도를 계산합니다."""
        try:
            embeddings = embedding_service.encode_texts([text1, text2], model)
            if embeddings is None or len(embeddings) < 2:
                return 0.0
            
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity for model {model}: {e}")
            return 0.0
    
    def test_scenario(self, scenario_name: str, test_cases: List[Tuple[str, str, float]]) -> Dict[str, Any]:
        """특정 시나리오에 대한 테스트를 실행합니다."""
        print(f"\n{'='*80}")
        print(f"🧪 테스트 시나리오: {scenario_name}")
        print(f"{'='*80}")
        
        results = {}
        
        for model in self.models:
            print(f"\n🤖 모델: {model}")
            print("-" * 60)
            
            model_results = {
                "similarities": [],
                "expected_similarities": [],
                "errors": [],
                "processing_times": []
            }
            
            for i, (text1, text2, expected_sim) in enumerate(test_cases, 1):
                start_time = time.time()
                
                try:
                    actual_sim = self.calculate_embedding_similarity(text1, text2, model)
                    processing_time = time.time() - start_time
                    
                    model_results["similarities"].append(actual_sim)
                    model_results["expected_similarities"].append(expected_sim)
                    model_results["processing_times"].append(processing_time)
                    
                    error = abs(actual_sim - expected_sim)
                    model_results["errors"].append(error)
                    
                    print(f"  테스트 {i}:")
                    print(f"    텍스트1: {text1[:50]}...")
                    print(f"    텍스트2: {text2[:50]}...")
                    print(f"    예상 유사도: {expected_sim:.3f}")
                    print(f"    실제 유사도: {actual_sim:.3f}")
                    print(f"    오차: {error:.3f}")
                    print(f"    처리 시간: {processing_time:.3f}초")
                    print()
                    
                except Exception as e:
                    logger.error(f"Error in test case {i} for model {model}: {e}")
                    model_results["errors"].append(1.0)  # 최대 오차로 처리
            
            # 모델별 통계 계산
            if model_results["similarities"]:
                avg_error = np.mean(model_results["errors"])
                correlation = pearsonr(model_results["expected_similarities"], 
                                     model_results["similarities"])[0]
                spearman_corr = spearmanr(model_results["expected_similarities"], 
                                        model_results["similarities"])[0]
                avg_processing_time = np.mean(model_results["processing_times"])
                
                model_results.update({
                    "avg_error": avg_error,
                    "pearson_correlation": correlation,
                    "spearman_correlation": spearman_corr,
                    "avg_processing_time": avg_processing_time
                })
                
                print(f"📊 {model} 성능 요약:")
                print(f"  평균 오차: {avg_error:.3f}")
                print(f"  피어슨 상관계수: {correlation:.3f}")
                print(f"  스피어만 상관계수: {spearman_corr:.3f}")
                print(f"  평균 처리 시간: {avg_processing_time:.3f}초")
            
            results[model] = model_results
        
        return results

    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 시나리오를 실행합니다."""
        print("🚀 복잡한 문장을 사용한 임베딩 모델 유사도 검증 테스트 시작")
        print(f"📋 테스트할 모델: {', '.join(self.models)}")
        print(f"📊 총 {len(self.test_scenarios)}개 시나리오, {sum(len(cases) for cases in self.test_scenarios.values())}개 테스트 케이스")

        all_results = {}
        overall_start_time = time.time()

        for scenario_name, test_cases in self.test_scenarios.items():
            scenario_results = self.test_scenario(scenario_name, test_cases)
            all_results[scenario_name] = scenario_results

        total_time = time.time() - overall_start_time

        # 전체 결과 분석
        self.analyze_overall_results(all_results, total_time)

        return all_results

    def analyze_overall_results(self, all_results: Dict[str, Any], total_time: float):
        """전체 테스트 결과를 분석하고 요약합니다."""
        print(f"\n{'='*80}")
        print("📈 전체 테스트 결과 분석")
        print(f"{'='*80}")

        model_summary = {}

        for model in self.models:
            all_errors = []
            all_correlations = []
            all_spearman_correlations = []
            all_processing_times = []

            for scenario_name, scenario_results in all_results.items():
                if model in scenario_results:
                    model_result = scenario_results[model]
                    if 'avg_error' in model_result:
                        all_errors.append(model_result['avg_error'])
                        all_correlations.append(model_result['pearson_correlation'])
                        all_spearman_correlations.append(model_result['spearman_correlation'])
                        all_processing_times.extend(model_result['processing_times'])

            if all_errors:
                model_summary[model] = {
                    "overall_avg_error": np.mean(all_errors),
                    "overall_pearson_correlation": np.mean(all_correlations),
                    "overall_spearman_correlation": np.mean(all_spearman_correlations),
                    "overall_avg_processing_time": np.mean(all_processing_times),
                    "total_processing_time": np.sum(all_processing_times),
                    "scenario_count": len(all_errors)
                }

        # 결과 출력
        print(f"⏱️  총 테스트 시간: {total_time:.2f}초")
        print()

        for model, summary in model_summary.items():
            print(f"🤖 {model}:")
            print(f"  전체 평균 오차: {summary['overall_avg_error']:.3f}")
            print(f"  전체 피어슨 상관계수: {summary['overall_pearson_correlation']:.3f}")
            print(f"  전체 스피어만 상관계수: {summary['overall_spearman_correlation']:.3f}")
            print(f"  평균 처리 시간: {summary['overall_avg_processing_time']:.3f}초")
            print(f"  총 처리 시간: {summary['total_processing_time']:.2f}초")
            print()

        # 모델 비교
        if len(model_summary) > 1:
            print("🏆 모델 비교 결과:")

            # 가장 낮은 오차를 가진 모델
            best_accuracy_model = min(model_summary.keys(),
                                    key=lambda m: model_summary[m]['overall_avg_error'])
            print(f"  가장 정확한 모델 (낮은 오차): {best_accuracy_model}")

            # 가장 높은 상관계수를 가진 모델
            best_correlation_model = max(model_summary.keys(),
                                       key=lambda m: model_summary[m]['overall_pearson_correlation'])
            print(f"  가장 일관된 모델 (높은 상관계수): {best_correlation_model}")

            # 가장 빠른 모델
            fastest_model = min(model_summary.keys(),
                              key=lambda m: model_summary[m]['overall_avg_processing_time'])
            print(f"  가장 빠른 모델: {fastest_model}")

        # 시나리오별 성능 분석
        print("\n📊 시나리오별 성능 분석:")
        for scenario_name, scenario_results in all_results.items():
            print(f"\n  {scenario_name}:")
            for model in self.models:
                if model in scenario_results and 'avg_error' in scenario_results[model]:
                    result = scenario_results[model]
                    print(f"    {model}: 오차 {result['avg_error']:.3f}, "
                          f"상관계수 {result['pearson_correlation']:.3f}")

    def save_results_to_file(self, results: Dict[str, Any], filename: str = "embedding_similarity_test_results.json"):
        """테스트 결과를 파일로 저장합니다."""
        try:
            # numpy 배열을 리스트로 변환
            serializable_results = {}
            for scenario, scenario_data in results.items():
                serializable_results[scenario] = {}
                for model, model_data in scenario_data.items():
                    serializable_results[scenario][model] = {}
                    for key, value in model_data.items():
                        if isinstance(value, np.ndarray):
                            serializable_results[scenario][model][key] = value.tolist()
                        elif isinstance(value, (np.float64, np.float32)):
                            serializable_results[scenario][model][key] = float(value)
                        else:
                            serializable_results[scenario][model][key] = value

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)

            print(f"📁 테스트 결과가 {filename}에 저장되었습니다.")

        except Exception as e:
            logger.error(f"결과 저장 중 오류 발생: {e}")


def main():
    """메인 테스트 실행 함수"""
    try:
        # 임베딩 서비스 초기화 확인
        print("🔧 임베딩 서비스 초기화 중...")

        # 사용 가능한 모델 확인
        available_models = embedding_service.get_available_models()
        print(f"📋 사용 가능한 모델: {[model['id'] for model in available_models]}")

        # 테스트 실행
        test_runner = ComplexEmbeddingSimilarityTest()
        results = test_runner.run_all_tests()

        # 결과 저장
        test_runner.save_results_to_file(results)

        print("\n✅ 모든 테스트가 완료되었습니다!")

    except Exception as e:
        logger.error(f"테스트 실행 중 오류 발생: {e}")
        raise


if __name__ == "__main__":
    main()
