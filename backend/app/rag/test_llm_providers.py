"""
LLM Provider 테스트 스크립트
Ollama와 OpenAI 모델을 테스트하는 간단한 스크립트
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.llm_factory import get_llm, list_supported_models


def test_llm(model_name: str):
    """LLM 모델 테스트"""
    print(f"\n{'=' * 80}")
    print(f" 테스트: {model_name} ".center(80, '='))
    print(f"{'=' * 80}\n")

    try:
        # LLM 인스턴스 생성
        llm = get_llm(model=model_name, temperature=0.0)
        print(f"✅ LLM 인스턴스 생성 성공")
        print(f"   - 타입: {type(llm).__name__}")

        # 간단한 테스트 쿼리
        from langchain_core.messages import HumanMessage

        test_message = "안녕하세요. 간단하게 '테스트 성공'이라고만 답변해주세요."
        print(f"\n📝 테스트 쿼리: {test_message[:50]}...")

        response = llm.invoke([HumanMessage(content=test_message)])
        print(f"✅ 응답 수신 성공")
        print(f"\n💬 응답 내용:")
        print(f"   {response.content}\n")

        return True

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""
    print("\n" + "=" * 80)
    print(" Guardcap LLM Provider 테스트 ".center(80, "="))
    print("=" * 80)

    # 지원 모델 목록 출력
    list_supported_models()

    # 테스트할 모델 선택
    print("\n테스트 옵션:")
    print("  1. Ollama (llama3)")
    print("  2. OpenAI (gpt-3.5-turbo) - OPENAI_API_KEY 필요")
    print("  3. 사용자 지정 모델")
    print("  4. 모두 건너뛰기\n")

    choice = input("선택 (1-4): ").strip()

    if choice == "1":
        test_llm("llama3")

    elif choice == "2":
        if not os.getenv("OPENAI_API_KEY"):
            print("\n⚠️  경고: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            print("   export OPENAI_API_KEY=sk-...")
            return

        test_llm("gpt-3.5-turbo")

    elif choice == "3":
        model = input("모델명 입력: ").strip()
        test_llm(model)

    else:
        print("\n테스트를 건너뜁니다.")

    print("\n" + "=" * 80)
    print(" 테스트 완료 ".center(80, "="))
    print("=" * 80)
    print("\n💡 Tip: 환경 변수로 모델을 설정할 수 있습니다:")
    print("   export LLM_MODEL=gpt-4")
    print("   export OPENAI_API_KEY=sk-...")
    print("   python main_agent.py\n")


if __name__ == "__main__":
    main()
