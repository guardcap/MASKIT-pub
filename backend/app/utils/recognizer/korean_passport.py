import re
from typing import List
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

class PassportRecognizer(EntityRecognizer):
    # 여권번호 정규식
    PASSPORT_REGEX_1 = r"([MSROD]\d{8})"       # M12345678
    PASSPORT_REGEX_2 = r"([MSROD]\d{3}[a-zA-Z]\d{4})"  # M123A1234
    KEYWORDS = ['여권번호', '여권', 'passport']

    def __init__(self):  
        super().__init__(name="passport_recognizer", supported_entities=["PASSPORT"])

    def analyze(self, text: str) -> EntityGroup:
        entities: List[Entity] = []

        # 전체 텍스트 스캔
        for regex in [self.PASSPORT_REGEX_1, self.PASSPORT_REGEX_2]:
            for match in re.finditer(regex, text):
                entity = Entity(
                    entity="PASSPORT",
                    word=match.group(),
                    start=match.start(),
                    end=match.end(),
                    score=1.0
                )
                entities.append(entity)

        # 키워드 주변 50자 내 스캔
        for keyword in self.KEYWORDS:
            for k_match in re.finditer(keyword, text, re.IGNORECASE):
                start_context = max(0, k_match.start() - 50)
                end_context = k_match.end() + 50
                context = text[start_context:end_context]

                for regex in [self.PASSPORT_REGEX_1, self.PASSPORT_REGEX_2]:
                    for match in re.finditer(regex, context):
                        abs_start = start_context + match.start()
                        abs_end = start_context + match.end()
                        # 중복 제거: word + start 기준
                        if not any(e.word == match.group() and e.start == abs_start for e in entities):
                            entities.append(Entity(
                                entity="PASSPORT",
                                word=match.group(),
                                start=abs_start,
                                end=abs_end,
                                score=1.0
                            ))

        return EntityGroup(entities)
