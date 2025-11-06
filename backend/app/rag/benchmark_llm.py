"""
LLM 성능 비교 벤치마크 테스트
Ollama llama3 vs OpenAI gpt-4o 비교

실행 방법:
    # OpenAI 사용 시 API 키 설정 필요
    export OPENAI_API_KEY=sk-proj-...
    python benchmark_llm.py
"""
import os
import sys
import time
from typing import Dict, List, Tuple
from statistics import mean, median, stdev

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.llm_factory import get_llm
from langchain_core.messages import HumanMessage, SystemMessage


# 테스트 케이스 정의
TEST_CASES = [
    {
        "name": "간단한 분류 작업",
        "system": "당신은 이메일 분류 전문가입니다.",
        "prompt": """다음 이메일의 발신자 유형을 분류하세요:
이메일: "안녕하세요, 김철수 고객님. 견적서를 보내드립니다."

다음 중 하나로 답변: internal, external_customer, external_partner, unknown
답변만 출력하세요.""",
        "expected_tokens": 10
    },
    {
        "name": "중간 복잡도 추론",
        "system": "당신은 개인정보 보호 전문가입니다.",
        "prompt": """다음 상황에서 전화번호를 마스킹해야 하는지 판단하세요:

상황: 외부 고객이 먼저 문의 이메일을 보냈고, 회사 담당자가 회신하는 중입니다.
전화번호: 담당자의 회사 전화번호 (02-1234-5678)

마스킹 필요 여부와 이유를 50자 이내로 설명하세요.""",
        "expected_tokens": 50
    },
    {
        "name": "복잡한 법률 해석",
        "system": "당신은 한국 개인정보보호법 전문가입니다.",
        "prompt": """개인정보보호법 제15조 1항 1호에 따르면:
"정보주체의 동의를 받은 경우 개인정보를 수집할 수 있다"

질문: 고객이 먼저 견적 요청 이메일을 보낸 경우, 이것이 '명시적 동의'로 간주될 수 있나요?
법적 근거와 함께 150자 이내로 답변하세요.""",
        "expected_tokens": 150
    },
    {
        "name": "긴 텍스트 생성",
        "system": "당신은 이메일 마스킹 정책 작성자입니다.",
        "prompt": """다음 PII 마스킹 결정에 대한 상세한 설명을 작성하세요:

PII: 이름 "김철수"
맥락: 외부 협력사에게 보내는 프로젝트 담당자 정보 공유 이메일
결정: 마스킹하지 않음

다음 항목을 포함하여 300자 이내로 설명:
1. 법적 근거
2. 비즈니스 정당성
3. 리스크 평가
4. 권고사항""",
        "expected_tokens": 300
    },
    {
        "name": "구조화된 출력",
        "system": "당신은 데이터 구조 전문가입니다.",
        "prompt": """다음 이메일에서 PII를 추출하고 JSON 형식으로 출력하세요:

이메일: "안녕하세요, 홍길동 고객님. 연락처 010-1234-5678로 회신드립니다."

출력 형식:
{
  "entities": [
    {"type": "NAME", "value": "...", "confidence": 0.0-1.0},
    {"type": "PHONE", "value": "...", "confidence": 0.0-1.0}
  ]
}

JSON만 출력하세요.""",
        "expected_tokens": 100
    }
]


class LLMBenchmark:
    """LLM 성능 벤치마크 클래스"""

    def __init__(self):
        self.results = {}

    def test_llm_latency(
        self,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        num_runs: int = 3
    ) -> Dict:
        """
        단일 LLM 테스트 실행

        Args:
            model_name: 모델명 (예: "llama3", "gpt-4o")
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            num_runs: 반복 실행 횟수

        Returns:
            결과 딕셔너리
        """
        latencies = []
        responses = []
        errors = 0

        print(f"\n   Testing {model_name}...", end=" ", flush=True)

        for run in range(num_runs):
            try:
                # LLM 인스턴스 생성
                llm = get_llm(model=model_name, temperature=0.0)

                # 메시지 구성
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]

                # 실행 시간 측정
                start_time = time.time()
                response = llm.invoke(messages)
                end_time = time.time()

                latency = end_time - start_time
                latencies.append(latency)
                responses.append(response.content)

                print(".", end="", flush=True)

            except Exception as e:
                print("X", end="", flush=True)
                errors += 1
                continue

        print(f" Done")

        if not latencies:
            return {
                "success": False,
                "error": "All runs failed",
                "errors": errors
            }

        return {
            "success": True,
            "model": model_name,
            "runs": num_runs,
            "errors": errors,
            "latencies": latencies,
            "mean_latency": mean(latencies),
            "median_latency": median(latencies),
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "stdev_latency": stdev(latencies) if len(latencies) > 1 else 0.0,
            "total_time": sum(latencies),
            "sample_response": responses[0][:100] if responses else None
        }

    def run_benchmark(
        self,
        models: List[str],
        num_runs: int = 3
    ) -> Dict:
        """
        전체 벤치마크 실행

        Args:
            models: 테스트할 모델 리스트
            num_runs: 각 테스트당 반복 실행 횟수

        Returns:
            전체 결과 딕셔너리
        """
        print("\n" + "=" * 80)
        print(" LLM 성능 비교 벤치마크 ".center(80, "="))
        print("=" * 80)
        print(f"\n📊 설정:")
        print(f"   - 테스트 케이스: {len(TEST_CASES)}개")
        print(f"   - 모델: {', '.join(models)}")
        print(f"   - 각 테스트당 실행 횟수: {num_runs}회")
        print(f"   - 총 API 호출: {len(TEST_CASES) * len(models) * num_runs}회\n")

        results = {}

        for test_case in TEST_CASES:
            test_name = test_case["name"]
            print(f"\n{'─' * 80}")
            print(f"📝 테스트: {test_name}")
            print(f"   예상 토큰: ~{test_case['expected_tokens']} tokens")

            test_results = {}

            for model in models:
                result = self.test_llm_latency(
                    model_name=model,
                    system_prompt=test_case["system"],
                    user_prompt=test_case["prompt"],
                    num_runs=num_runs
                )
                test_results[model] = result

            results[test_name] = test_results

        self.results = results
        return results

    def print_summary(self):
        """결과 요약 출력"""
        print("\n\n" + "=" * 80)
        print(" 📊 벤치마크 결과 요약 ".center(80, "="))
        print("=" * 80)

        if not self.results:
            print("\n❌ 결과가 없습니다.")
            return

        # 모델별 전체 평균 계산
        all_models = set()
        for test_results in self.results.values():
            all_models.update(test_results.keys())

        model_stats = {model: [] for model in all_models}

        for test_name, test_results in self.results.items():
            print(f"\n{'─' * 80}")
            print(f"📝 {test_name}")
            print(f"{'─' * 80}")

            for model, result in test_results.items():
                if not result.get("success"):
                    print(f"\n❌ {model}: 실패 ({result.get('error', 'Unknown error')})")
                    continue

                mean_lat = result['mean_latency']
                model_stats[model].append(mean_lat)

                print(f"\n✅ {model}:")
                print(f"   평균 지연시간: {mean_lat:.3f}초")
                print(f"   중앙값: {result['median_latency']:.3f}초")
                print(f"   최소/최대: {result['min_latency']:.3f}초 / {result['max_latency']:.3f}초")
                print(f"   표준편차: {result['stdev_latency']:.3f}초")
                print(f"   실패: {result['errors']}/{result['runs']}회")
                print(f"   샘플 응답: {result['sample_response']}...")

        # 전체 평균 비교
        print(f"\n\n" + "=" * 80)
        print(" 🏆 전체 평균 비교 ".center(80, "="))
        print("=" * 80)

        sorted_models = sorted(
            model_stats.items(),
            key=lambda x: mean(x[1]) if x[1] else float('inf')
        )

        for rank, (model, latencies) in enumerate(sorted_models, 1):
            if not latencies:
                print(f"\n{rank}. {model}: 데이터 없음")
                continue

            avg_latency = mean(latencies)
            total_time = sum(latencies)

            print(f"\n{rank}. {model}:")
            print(f"   평균 지연시간: {avg_latency:.3f}초")
            print(f"   총 실행 시간: {total_time:.2f}초")
            print(f"   테스트 케이스: {len(latencies)}개")

            # 1등 대비 속도 계산
            if rank == 1:
                baseline = avg_latency
                print(f"   🥇 가장 빠름!")
            else:
                slower_by = (avg_latency / baseline - 1) * 100
                print(f"   📊 1등보다 {slower_by:.1f}% 느림")

        print("\n" + "=" * 80)

    def export_csv(self, filename: str = "benchmark_results.csv"):
        """결과를 CSV로 내보내기"""
        import csv

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Test Case',
                'Model',
                'Mean Latency (s)',
                'Median Latency (s)',
                'Min Latency (s)',
                'Max Latency (s)',
                'Stdev (s)',
                'Errors',
                'Runs'
            ])

            for test_name, test_results in self.results.items():
                for model, result in test_results.items():
                    if not result.get('success'):
                        continue

                    writer.writerow([
                        test_name,
                        model,
                        f"{result['mean_latency']:.3f}",
                        f"{result['median_latency']:.3f}",
                        f"{result['min_latency']:.3f}",
                        f"{result['max_latency']:.3f}",
                        f"{result['stdev_latency']:.3f}",
                        result['errors'],
                        result['runs']
                    ])

        print(f"\n💾 결과가 {filename}에 저장되었습니다.")


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="LLM 성능 비교 벤치마크")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["llama3", "gpt-4o"],
        help="테스트할 모델 (기본값: llama3 gpt-4o)"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="각 테스트당 반복 실행 횟수 (기본값: 3)"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="결과를 CSV로 내보내기"
    )
    parser.add_argument(
        "--skip-api-check",
        action="store_true",
        help="API 키 체크 건너뛰기 (테스트용, OpenAI 호출 실패 예상)"
    )

    args = parser.parse_args()

    # OpenAI 사용 시 API 키 체크
    if any("gpt" in model or "openai" in model for model in args.models):
        if not os.getenv("OPENAI_API_KEY"):
            if not args.skip_api_check:
                print("\n❌ 오류: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
                print("\n해결 방법:")
                print("  1. OpenAI API 키 설정:")
                print("     export OPENAI_API_KEY=sk-proj-...")
                print("\n  2. 또는 --skip-api-check 플래그 사용 (OpenAI 테스트 실패 예상):")
                print("     python benchmark_llm.py --models llama3 gpt-4o --skip-api-check")
                print("\n  3. 또는 Ollama 모델만 테스트:")
                print("     python benchmark_llm.py --models llama3\n")
                sys.exit(1)
            else:
                print("\n⚠️  경고: OPENAI_API_KEY가 설정되지 않았습니다.")
                print("   --skip-api-check 플래그로 인해 계속 실행하지만,")
                print("   OpenAI 모델 테스트는 실패할 것입니다.\n")

    # 벤치마크 실행
    benchmark = LLMBenchmark()

    try:
        benchmark.run_benchmark(
            models=args.models,
            num_runs=args.runs
        )

        # 결과 출력
        benchmark.print_summary()

        # CSV 내보내기
        if args.export:
            benchmark.export_csv()

    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단되었습니다.")
        return

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    print("\n✅ 벤치마크 완료!\n")


if __name__ == "__main__":
    main()
