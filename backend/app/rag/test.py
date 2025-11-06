import unittest
from unittest.mock import patch, MagicMock, ANY

# main.py 스크립트의 함수와 Entity 클래스를 임포트합니다.
import main
from scripts.llm_client import Entity

class TestGuardCapPipeline(unittest.TestCase):

    def setUp(self):
        """테스트에 사용될 5가지 샘플 데이터를 미리 정의합니다."""
        print(f"\n--- Setting up for test: {self._testMethodName} ---")
        
        self.samples = {
            "legal_priority_high_risk": {
                "doc_summary": "고객센터를 통해 개인정보(주민번호) 유출이 의심된다는 민원이 접수됨.",
                "checklist": {"긴급": True, "보안": True, "고객": True},
                "entities": [
                    Entity(entity="PII", score=0.99, word="주민번호", start=15, end=19),
                    Entity(entity="NAME", score=0.98, word="김철수", start=25, end=28)
                ]
            },
            "policy_priority_low_risk": {
                "doc_summary": "사내 기술 공유를 위한 AI 활용 세미나 개최 안내문 초안",
                "checklist": {"내부공유": True},
                "entities": [
                    Entity(entity="ORGANIZATION", score=0.9, word="AI팀", start=30, end=33)
                ]
            },
            "legal_priority_marketing": {
                "doc_summary": "SNS 경품 이벤트를 통해 신규 고객의 휴대폰 번호를 수집하려고 합니다.",
                "checklist": {"마케팅": True, "개인정보": True},
                "entities": [
                    Entity(entity="PHONE_NUMBER", score=0.95, word="휴대폰 번호", start=23, end=29)
                ]
            },
            "policy_priority_sensitive": {
                "doc_summary": "전사 조직 개편에 따른 일부 팀 해체 및 통합 공지 (대외비)",
                "checklist": {"인사": True, "대외비": True},
                "entities": [
                    Entity(entity="DEPARTMENT", score=0.99, word="알파팀", start=30, end=33),
                    Entity(entity="DEPARTMENT", score=0.99, word="베타팀", start=35, end=38)
                ]
            },
            "hybrid_customer_survey": {
                "doc_summary": "고객 만족도 조사를 위한 이메일 발송 및 참여자 대상 기프티콘 증정 안내",
                "checklist": {"고객": True, "마케팅": True},
                "entities": [
                    Entity(entity="EMAIL", score=0.98, word="이메일", start=16, end=19),
                    Entity(entity="NAME", score=0.92, word="고객명", start=25, end=28)
                ]
            }
        }

    @patch('main.DecisionEngine')
    @patch('main.GuardcapRetriever')
    @patch('main.generate_task_profile_with_llm')
    def test_legal_priority_scenario(self, mock_generate_profile, mock_retriever_cls, mock_engine_cls):
        """✅ 테스트 1: 개인정보 유출과 같이 법률이 우선시되는 시나리오"""
        # 1. Arrange (테스트 준비)
        sample = self.samples["legal_priority_high_risk"]
        
        # Mock LLM이 반환할 TaskProfile 설정
        mock_generate_profile.return_value = {
            "purpose": "SECURITY_INCIDENT", "category": "사외", "channel": "REPORT"
        }
        
        # Mock Retriever 인스턴스 및 검색 결과 설정
        mock_retriever = mock_retriever_cls.return_value
        mock_retriever.search_A_cases.return_value = []
        # 사내규정보다 법률의 DANGER 점수를 훨씬 높게 설정
        mock_retriever.search_B_policies.return_value = [
            {'source': 'B', 'CRITICAL_score': {'CRITICAL_지수': 1.5}, 'OPEN_score': {'OPEN_지수': 0}, 'score': 0.8, 'snippet': '내부 보안 사고 대응 매뉴얼...'}
        ]
        mock_retriever.search_C_laws.return_value = [
            {'source': 'C', 'CRITICAL_score': {'CRITICAL_지수': 5.0}, 'OPEN_score': {'OPEN_지수': 0}, 'score': 0.95, 'snippet': '개인정보보호법 제34조(개인정보 유출 통지)...'},
            {'source': 'C', 'CRITICAL_score': {'CRITICAL_지수': 4.5}, 'OPEN_score': {'OPEN_지수': 0}, 'score': 0.92, 'snippet': '정보통신망법 제28조(개인정보의 보호조치)...'}
        ]
        
        # Mock 결정 엔진 설정
        mock_engine = mock_engine_cls.return_value
        mock_engine.make_decision.return_value = {"decision": "CRITICAL", "reason": "법률 위반 가능성 높음"}

        # 2. Act (테스트 대상 함수 실행)
        main.run_guardcap_pipeline(sample, MagicMock(), "dummy_schema.json", "dummy_path")

        # 3. Assert (결과 검증)
        # 결정 엔진의 make_decision이 호출되었는지 확인
        mock_engine.make_decision.assert_called_once()
        # make_decision에 전달된 DANGER 점수가 법률(5.0 + 4.5)과 규정(1.5)의 합인 11.0인지 확인
        args, kwargs = mock_engine.make_decision.call_args
        self.assertAlmostEqual(kwargs['danger_score'], 11.0)

    @patch('main.DecisionEngine')
    @patch('main.GuardcapRetriever')
    @patch('main.generate_task_profile_with_llm')
    def test_policy_priority_scenario(self, mock_generate_profile, mock_retriever_cls, mock_engine_cls):
        """✅ 테스트 2: 사내 세미나 공지와 같이 내부 규정이 우선시되는 시나리오"""
        # 1. Arrange
        sample = self.samples["policy_priority_low_risk"]
        mock_generate_profile.return_value = {
            "purpose": "INTERNAL_ANNOUNCEMENT", "category": "사내", "channel": "EMAIL"
        }
        mock_retriever = mock_retriever_cls.return_value
        # 법률 근거는 거의 없고, 사내 규정 점수가 더 높게 설정
        mock_retriever.search_A_cases.return_value = [{'source': 'A'}]
        mock_retriever.search_B_policies.return_value = [
            {'source': 'B', 'CRITICAL_score': {'CRITICAL_지수': 0.5}, 'OPEN_score': {'OPEN_지수': 2.0}, 'score': 0.9, 'snippet': '사내 커뮤니케이션 가이드라인...'}
        ]
        mock_retriever.search_C_laws.return_value = []

        mock_engine = mock_engine_cls.return_value
        mock_engine.make_decision.return_value = {"decision": "SAFE", "reason": "유사 사례 및 내부 규정 준수"}
        
        # 2. Act
        main.run_guardcap_pipeline(sample, MagicMock(), "dummy_schema.json", "dummy_path")

        # 3. Assert
        mock_engine.make_decision.assert_called_once()
        # DANGER 점수가 내부규정(0.5)에서만 발생했는지 확인
        args, kwargs = mock_engine.make_decision.call_args
        self.assertAlmostEqual(kwargs['danger_score'], 0.5)
        self.assertAlmostEqual(kwargs['safe_score'], 2.0)
        # 유사 사례(A_cases)가 1건 전달되었는지 확인
        self.assertEqual(len(kwargs['a_case_results']), 1)
        
    @patch('main.DecisionEngine')
    @patch('main.GuardcapRetriever')
    @patch('main.generate_task_profile_with_llm')
    def test_sensitive_policy_scenario(self, mock_generate_profile, mock_retriever_cls, mock_engine_cls):
        """✅ 테스트 3: 조직 개편과 같이 법률보다 민감한 내부 규정이 중요한 시나리오"""
        # 1. Arrange
        sample = self.samples["policy_priority_sensitive"]
        mock_generate_profile.return_value = {
            "purpose": "HR_CHANGE", "category": "사내", "channel": "EMAIL"
        }
        mock_retriever = mock_retriever_cls.return_value
        # 관련 법률은 없지만, '대외비' 관련 내부 규정 위반 위험 점수를 높게 설정
        mock_retriever.search_A_cases.return_value = []
        mock_retriever.search_B_policies.return_value = [
            {'source': 'B', 'CRITICAL_score': {'CRITICAL_지수': 4.0}, 'OPEN_score': {'OPEN_지수': 0}, 'score': 0.95, 'snippet': '대외비 및 민감 정보 취급 규정...'},
            {'source': 'B', 'CRITICAL_score': {'CRITICAL_지수': 3.0}, 'OPEN_score': {'OPEN_지수': 0}, 'score': 0.90, 'snippet': '인사 관련 공지 가이드라인...'}
        ]
        mock_retriever.search_C_laws.return_value = []

        mock_engine = mock_engine_cls.return_value
        mock_engine.make_decision.return_value = {"decision": "CAUTION", "reason": "내부 민감 정보 포함"}
        
        # 2. Act
        main.run_guardcap_pipeline(sample, MagicMock(), "dummy_schema.json", "dummy_path")

        # 3. Assert
        mock_engine.make_decision.assert_called_once()
        # DANGER 점수가 내부 규정 점수들의 합(4.0 + 3.0)인지 확인
        args, kwargs = mock_engine.make_decision.call_args
        self.assertAlmostEqual(kwargs['danger_score'], 7.0)

    # 나머지 두 샘플에 대한 테스트 케이스도 위와 같은 패턴으로 추가할 수 있습니다.
    # 여기서는 대표적인 3가지 케이스만 작성했습니다.

if __name__ == '__main__':
    unittest.main(verbosity=2)