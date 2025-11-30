import unittest
from utils.filtering_LLM.core import run
from utils.filtering_LLM.models import Meta, ContextPack, RuleChunk
from utils.entity import Entity, EntityGroup

def mock_get_context_pack(queries, filters):
    """테스트용 mock RAG 응답"""
    return ContextPack(chunks=[
        RuleChunk(
            chunk_id="law1",
            cluster_id="privacy_law",
            doc_id="privacy_act",
            source_type="LAW",
            jurisdiction="KR",
            text="개인정보는 수집 목적에 필요한 최소한의 범위 내에서만 제공되어야 한다."
        ),
        RuleChunk(
            chunk_id="policy1",
            cluster_id="company_policy",
            doc_id="security_guidelines",
            source_type="INTERNAL_POLICY",
            jurisdiction="KR",  # jurisdiction 필드 추가
            text="외부 공개 시 전화번호는 반드시 마스킹 처리해야 한다."
        ),
        RuleChunk(
            chunk_id="guide1",
            cluster_id="masking_guide",
            doc_id="privacy_guidelines",
            source_type="GOV_GUIDE",
            jurisdiction="KR",
            text="계좌번호는 마지막 4자리를 제외하고 마스킹하며, 이메일은 @ 앞부분을 마스킹한다."
        )
    ])

class TestFilteringLLM(unittest.TestCase):
    def setUp(self):
        # 테스트 데이터 설정
        self.meta = Meta(
            sender_team="고객지원팀",
            sender_role="상담사",
            recipient_domain="external",
            purpose="고객응대",
            audience="external"
        )
        
        self.entities = [
            Entity(
                entity="PHONE_NUMBER",
                score=0.99,
                word="010-1234-5678",
                start=0,
                end=13,
                pageIndex=1,
                bbox=(100, 100, 200, 120)
            ),
            Entity(
                entity="EMAIL",
                score=0.98,
                word="test@example.com",
                start=20,
                end=35,
                pageIndex=1,
                bbox=(300, 100, 400, 120)
            ),
            Entity(
                entity="ACCOUNT_NUMBER",
                score=0.97,
                word="123-456-789012",
                start=40,
                end=54,
                pageIndex=1,
                bbox=(500, 100, 600, 120)
            )
        ]
        self.entity_group = EntityGroup(self.entities)

    def test_external_masking_rules(self):
        """외부 공개 시 마스킹 규칙 테스트"""
        # 1) LLM 판단 요청
        masked_group = run(
            meta=self.meta,
            entity_group=self.entity_group,
            get_context_pack=mock_get_context_pack
        )

        # 2) 결과 검증
        entities_by_type = {e.entity: e for e in masked_group.entities}
        
        # 전화번호는 반드시 완전 마스킹
        phone = entities_by_type.get("PHONE_NUMBER")
        self.assertIsNotNone(phone)
        self.assertEqual(getattr(phone, "masking_method", None), "mask_full")
        
        # 이메일은 부분 마스킹 (업무상 필요)
        email = entities_by_type.get("EMAIL")
        self.assertIsNotNone(email)
        self.assertEqual(getattr(email, "masking_method", None), "mask_partial")
        self.assertIn("keep_domain", getattr(email, "masking_format", {}))
        
        # 계좌번호는 부분 마스킹 (기본 정책)
        account = entities_by_type.get("ACCOUNT_NUMBER")
        self.assertIsNotNone(account)
        self.assertEqual(getattr(account, "masking_method", None), "mask_partial")
        self.assertEqual(getattr(account, "masking_format", {}).get("keep_last"), 4)
        self.assertEqual(getattr(account, "masking_format", {}).get("separator"), "-")

    def test_internal_masking_rules(self):
        """내부 공개 시 마스킹 규칙 테스트"""
        self.meta.audience = "internal_limited"
        
        masked_group = run(
            meta=self.meta,
            entity_group=self.entity_group,
            get_context_pack=mock_get_context_pack
        )

        entities_by_type = {e.entity: e for e in masked_group.entities}
        
        # 내부라도 계좌번호는 부분 마스킹
        account = entities_by_type.get("ACCOUNT_NUMBER")
        self.assertIsNotNone(account)
        self.assertEqual(getattr(account, "masking_method", None), "mask_partial")
        
        # 나머지는 유지
        for entity_type in ["PHONE_NUMBER", "EMAIL"]:
            entity = entities_by_type.get(entity_type)
            self.assertIsNotNone(entity)
            self.assertEqual(getattr(entity, "masking_method", None), "keep")

    def test_heuristic_fallback(self):
        """LLM 실패 시 휴리스틱 폴백 테스트"""
        import os
        os.environ["FILTERING_LLM_FORCE_HEURISTIC"] = "1"
        
        masked_group = run(
            meta=self.meta,
            entity_group=self.entity_group,
            get_context_pack=mock_get_context_pack
        )

        entities_by_type = {e.entity: e for e in masked_group.entities}
        
        # 전화번호는 외부 공개 시 완전 마스킹
        phone = entities_by_type.get("PHONE_NUMBER")
        self.assertIsNotNone(phone)
        self.assertEqual(getattr(phone, "masking_method", None), "mask_full")
        
        # 계좌번호는 항상 부분 마스킹
        account = entities_by_type.get("ACCOUNT_NUMBER")
        self.assertIsNotNone(account)
        self.assertEqual(getattr(account, "masking_method", None), "mask_partial")
        self.assertEqual(getattr(account, "masking_format", {}).get("keep_last"), 4)
        self.assertEqual(getattr(account, "masking_format", {}).get("separator"), "-")
        
        os.environ["FILTERING_LLM_FORCE_HEURISTIC"] = "0"

if __name__ == "__main__":
    unittest.main()