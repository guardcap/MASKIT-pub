from typing import List, Optional
from app.utils.recognizer_registry import RecognizerRegistry
from app.utils.ner.NER_engine import NerEngine
from app.utils.entity import Entity, EntityGroup

class AnalyzerEngine:
    """
    규칙 기반(RecognizerRegistry) + NER 기반(NerEngine) 결과를
    하나의 EntityGroup으로 통합하여 반환.
    """
    def __init__(self, db_client=None):
        print("...AnalyzerEngine 초기화 중...")
        self.registry = RecognizerRegistry(db_client=db_client)
        self.registry.load_predefined_recognizers()

        # 커스텀 엔티티 로드 (비동기)
        self.db_client = db_client
        self.custom_loaded = False

        self.nlp_engine = NerEngine()
        print("~AnalyzerEngine 준비 완료~")

    async def load_custom_entities(self):
        """커스텀 엔티티를 MongoDB에서 로드 (비동기)"""
        if self.db_client and not self.custom_loaded:
            await self.registry.load_custom_recognizers()
            self.custom_loaded = True
            print("✅ 커스텀 엔티티 로드 완료")

    def analyze(self, text: str) -> EntityGroup:
        # 1) 규칙 기반 결과
        regex_group = self.registry.regex_analyze(text)

        # 2) NER 결과
        ner_group = self.nlp_engine.ner_analyze(text)

        # 3) 병합
        combined = self._merge_groups(regex_group, ner_group)

        # 4) (선택) 동일 범위/동일 타입 중복 정리 및 정렬
        combined.entities = self._dedup_and_sort(combined.entities)

        # 로그 출력
        print("\n\n✨ 최종 분석 결과(EntityGroup):")
        for e in combined.entities:
            print(f" - {e.entity}: '{e.word}' ({e.start}, {e.end}) score={e.score:.2f}")

        return combined

    @staticmethod
    def _merge_groups(a: EntityGroup, b: EntityGroup) -> EntityGroup:
        # RecognizerRegistry의 병합 정책을 재사용하기 위해 간단 델리게이션
        # (코드 중복 방지를 위해 RecognizerRegistry._merge_groups를 가져와도 됨)
        merged = EntityGroup(list(a.entities))
        for e in b.entities:
            # 간단 병합: 타입이 같고 겹치면 긴 span/높은 score 우선
            replaced = False
            for i, ea in enumerate(merged.entities):
                if ea.entity == e.entity and (ea.start < e.end and e.start < ea.end):
                    len_a = ea.end - ea.start
                    len_b = e.end - e.start
                    if len_b > len_a or (len_b == len_a and e.score > ea.score):
                        merged.entities[i] = e
                    replaced = True
                    break
            if not replaced:
                merged.entities.append(e)
        return merged

    @staticmethod
    def _dedup_and_sort(entities: List[Entity]) -> List[Entity]:
        # 완전 동일한 (entity, start, end, word) 중복 제거
        seen = set()
        uniq: List[Entity] = []
        for e in entities:
            key = (e.entity, e.start, e.end, e.word)
            if key in seen:
                continue
            seen.add(key)
            uniq.append(e)
        uniq.sort(key=lambda x: (x.start, x.end))
        return uniq
