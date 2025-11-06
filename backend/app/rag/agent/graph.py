"""
LangGraph 워크플로우 구성
각 노드를 연결하여 전체 에이전트 그래프를 생성
"""
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import AgentNodes
from agent.retrievers import HybridRetriever


def create_masking_agent_graph(retriever: HybridRetriever, llm_model: str = "llama3"):
    """
    마스킹 에이전트 그래프 생성

    워크플로우:
    1. PII 탐지 (pii_detection)
    2. 맥락 분석 (context_analysis)
    3. 라우팅 (routing)
    4. 정보 검색 (information_retrieval)
    5. 추론 및 종합 (reasoning_and_synthesis)
    6. 최종 결정 (final_decision)
    """

    # 노드 인스턴스 생성
    nodes = AgentNodes(retriever=retriever, llm_model=llm_model)

    # StateGraph 생성
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("pii_detection", nodes.pii_detection_node)
    workflow.add_node("context_analysis", nodes.context_analysis_node)
    workflow.add_node("routing", nodes.routing_node)
    workflow.add_node("information_retrieval", nodes.information_retrieval_node)
    workflow.add_node("reasoning_and_synthesis", nodes.reasoning_and_synthesis_node)
    workflow.add_node("final_decision", nodes.final_decision_node)

    # 엣지 연결 (순차적 흐름)
    workflow.set_entry_point("pii_detection")
    workflow.add_edge("pii_detection", "context_analysis")
    workflow.add_edge("context_analysis", "routing")
    workflow.add_edge("routing", "information_retrieval")
    workflow.add_edge("information_retrieval", "reasoning_and_synthesis")
    workflow.add_edge("reasoning_and_synthesis", "final_decision")
    workflow.add_edge("final_decision", END)

    # 그래프 컴파일
    app = workflow.compile()

    return app


def run_masking_pipeline(email: str, retriever: HybridRetriever, llm_model: str = "llama3") -> dict:
    """
    전체 마스킹 파이프라인 실행

    Args:
        email: 원본 이메일 텍스트
        retriever: HybridRetriever 인스턴스
        llm_model: 사용할 LLM 모델명

    Returns:
        dict: 최종 결과 (masked_email, decisions, risk_level 등)
    """
    # 그래프 생성
    app = create_masking_agent_graph(retriever, llm_model)

    # 초기 상태
    initial_state = {
        'original_email': email,
        'detected_piis': [],
        'email_context': None,
        'retrieved_guides': [],
        'retrieved_laws': [],
        'retrieved_policies': [],
        'retrieved_cases': [],
        'reasoning_steps': [],
        'masking_decisions': [],
        'masked_email': '',
        'risk_level': 'unknown',
        'should_block': False,
        'warnings': []
    }

    print("\n" + "=" * 80)
    print(" 🤖 Guardcap Agentic Masking Pipeline 시작 ".center(80, "="))
    print("=" * 80)

    # 그래프 실행
    final_state = app.invoke(initial_state)

    print("\n" + "=" * 80)
    print(" 📊 최종 결과 ".center(80, "="))
    print("=" * 80)

    # 결과 출력
    result = {
        'original_email': email,
        'masked_email': final_state['masked_email'],
        'risk_level': final_state['risk_level'],
        'should_block': final_state['should_block'],
        'detected_piis_count': len(final_state['detected_piis']),
        'masking_decisions': [
            {
                'pii_type': d.pii.entity_type,
                'pii_value': d.pii.value,
                'action': d.action,
                'reasoning': d.reasoning[:100] + '...' if len(d.reasoning) > 100 else d.reasoning,
                'confidence': d.confidence
            }
            for d in final_state['masking_decisions']
        ],
        'retrieved_guides_count': len(final_state['retrieved_guides']),
        'retrieved_laws_count': len(final_state['retrieved_laws']),
        'warnings': final_state.get('warnings', [])
    }

    # 콘솔 출력
    print(f"\n📧 원본 이메일:\n{email}\n")
    print(f"🔒 마스킹된 이메일:\n{result['masked_email']}\n")
    print(f"⚠️  위험도: {result['risk_level']}")
    print(f"🚫 차단 여부: {result['should_block']}")
    print(f"🔍 탐지된 PII: {result['detected_piis_count']}개")
    print(f"📚 검색된 가이드: {result['retrieved_guides_count']}개")
    print(f"⚖️  검색된 법률: {result['retrieved_laws_count']}개")

    if result['warnings']:
        print(f"\n⚠️  경고:")
        for warning in result['warnings']:
            print(f"   - {warning}")

    print(f"\n💡 마스킹 결정:")
    for decision in result['masking_decisions']:
        print(f"   • {decision['pii_type']} '{decision['pii_value']}' → {decision['action']}")
        print(f"     근거: {decision['reasoning']}")

    print("\n" + "=" * 80)

    return result
