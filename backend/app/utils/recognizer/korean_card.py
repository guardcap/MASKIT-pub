import re
from typing import List
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

class CardNumberRecognizer(EntityRecognizer):
    # 카드번호 예시: 1234-5678-9012-3456 또는 1234567890123456 (16자리)
    CARD_REGEX = r"(?:\d{4}[-.\s]?){3}\d{4}"
    KEYWORDS = ['카드번호', '카드', 'credit card', 'card']

    def __init__(self):
        super().__init__(name="card_recognizer", supported_entities=["CARD_NUMBER"])
        self.card_regex = re.compile(self.CARD_REGEX)
        self.keyword_regexes = [re.compile(k, re.IGNORECASE) for k in self.KEYWORDS]

    def analyze(self, text: str) -> EntityGroup:
        entities: List[Entity] = []

        # 전체 텍스트 스캔
        for match in self.card_regex.finditer(text):
            start, end = match.start(), match.end()
            # 중복 제거: 기존 범위 포함/겹침 체크
            if any((e.start <= start < e.end) or (start <= e.start < end) for e in entities):
                continue
            entities.append(Entity(
                entity="CARD_NUMBER",
                word=match.group(),
                start=start,
                end=end,
                score=1.0
            ))

        # 키워드 주변 탐지 (앞뒤 30~60자)
        for kw_re in self.keyword_regexes:
            for k_match in kw_re.finditer(text):
                start_context = max(0, k_match.start() - 30)
                end_context = k_match.end() + 60
                context = text[start_context:end_context]

                for match in self.card_regex.finditer(context):
                    abs_start = start_context + match.start()
                    abs_end = start_context + match.end()
                    if any((e.start <= abs_start < e.end) or (abs_start <= e.start < abs_end) for e in entities):
                        continue
                    entities.append(Entity(
                        entity="CARD_NUMBER",
                        word=match.group(),
                        start=abs_start,
                        end=abs_end,
                        score=1.0
                    ))

        return EntityGroup(entities)
