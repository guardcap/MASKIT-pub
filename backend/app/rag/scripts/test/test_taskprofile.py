import unittest
import json
import os
import sys
from unittest.mock import patch



# --- 실제 모듈과 클래스를 임포트 ---
from scripts.llm_taskprofile import TaskProfileGenerator
# 이제 Mock이 아닌 실제 LLMClient와 Entity 클래스를 임포트합니다.
from scripts.llm_client import LLMClient, Entity

class TestTaskProfileGeneratorIntegration(unittest.TestCase):

    def setUp(self):
        """테스트 시작 전, 사용할 샘플 데이터와 의존성을 준비합니다."""
        self.schema_path = os.path.join('./schemas/TaskProfile.schema.json')
        
        # 실제 LLMClient 객체를 생성합니다. 네트워크 호출은 patch를 통해 제어됩니다.
        self.llm_client = LLMClient(model="test-model")
        
        # 사용자께서 제공한 샘플 데이터를 실제 Entity 클래스를 사용하여 구성합니다.
        self.samples = [
            {
                "doc_summary": "2025년 하반기 신입사원 최종 합격자 명단 공지",
                "checklist": {"중요": True},
                "entities": [
                    Entity(entity="NAME", score=0.99, word="김민지", start=105, end=108),
                    Entity(entity="NAME", score=0.99, word="박준호", start=110, end=113)
                ]
            },
            {
                "doc_summary": "신입사원 홍길동의 부서 이동 및 관련 담당자 안내 공지",
                "checklist": {},
                "entities": [
                    Entity(entity="NAME", score=0.99, word="홍길동", start=46, end=49),
                    Entity(entity="EMAIL", score=0.99, word="hong.gildong@example.com", start=70, end=95)
                ]
            }
        ]

    # `scripts.llm_client` 모듈에 있는 `ollama.chat` 함수의 동작을 가로챕니다.
    @patch('scripts.llm_client.ollama.chat')
    def test_successful_generation_with_real_llm_client(self, mock_ollama_chat):
        """✅ 실제 LLMClient와 TaskProfileGenerator를 연동한 성공 케이스 테스트"""
        print("\n===== 통합 테스트: 성공 케이스 =====")
        sample = self.samples[0]
        
        # 1. Arrange: Mock ollama.chat이 반환할 가상 응답을 설정합니다.
        # LLMClient는 이 응답의 'message.content'를 파싱하게 됩니다.
        llm_output_json = {
            "category": "사내", "audience": "EMPLOYEE", "channel": "EMAIL",
            "purpose": "ANNOUNCEMENT", "legal_priority": "POLICY_OVER_LAW",
            "task_type": "신입사원 최종 합격 공지"
        }
        mock_ollama_chat.return_value = {
            "message": {"content": json.dumps(llm_output_json)}
        }
        
        # 2. Act: 실제 TaskProfileGenerator에 실제 LLMClient를 주입하여 실행합니다.
        generator = TaskProfileGenerator(llm=self.llm_client, schema_path=self.schema_path)
        profile = generator.generate(sample["checklist"], sample["entities"], sample["doc_summary"])

        # 3. Assert: 최종 결과와 Mock의 호출 여부를 검증합니다.
        self.assertEqual(profile["purpose"], "ANNOUNCEMENT")
        self.assertEqual(profile["task_type"], "신입사원 최종 합격 공지")
        mock_ollama_chat.assert_called_once() # ollama.chat이 정확히 1번 호출되었는지 확인

    @patch('scripts.llm_client.ollama.chat')
    def test_retry_logic_with_real_llm_client(self, mock_ollama_chat):
        """✅ 스키마 검증 실패 후 재시도 로직 통합 테스트"""
        print("\n===== 통합 테스트: 재시도 케이스 =====")
        sample = self.samples[1]
        
        # 1. Arrange: 첫 번째는 잘못된 응답, 두 번째는 올바른 응답을 반환하도록 설정
        invalid_json_str = json.dumps({"purpose": "HR_MOVE", "audience": "INVALID_VALUE"})
        valid_json_str = json.dumps({
            "category": "사내", "audience": "EMPLOYEE", "channel": "EMAIL",
            "purpose": "HR_MOVE", "legal_priority": "POLICY_OVER_LAW",
            "task_type": "신규입사자 부서 배치 안내"
        })
        
        mock_ollama_chat.side_effect = [
            {"message": {"content": invalid_json_str}}, # 첫 번째 호출 시 반환값
            {"message": {"content": valid_json_str}}    # 두 번째 호출 시 반환값
        ]

        # 2. Act
        generator = TaskProfileGenerator(llm=self.llm_client, schema_path=self.schema_path)
        profile = generator.generate(sample["checklist"], sample["entities"], sample["doc_summary"])

        # 3. Assert
        self.assertEqual(profile["purpose"], "HR_MOVE")
        self.assertEqual(profile["task_type"], "신규입사자 부서 배치 안내")
        # ollama.chat이 재시도를 포함해 총 2번 호출되었는지 확인
        self.assertEqual(mock_ollama_chat.call_count, 2)

if __name__ == '__main__':
    unittest.main(verbosity=2)