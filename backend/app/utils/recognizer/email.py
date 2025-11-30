import re
from typing import List
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

class EmailRecognizer(EntityRecognizer):
    EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    KEYWORDS = ['이메일', '메일', 'email']

    def __init__(self):  
        super().__init__(name="email_recognizer", supported_entities=["EMAIL"])

    def analyze(self, text: str) -> EntityGroup:
        """
        주어진 텍스트에서 이메일을 분석하고 EntityGroup으로 반환
        """
        entities = []

        # 텍스트 전체에서 이메일 찾기
        for match in re.finditer(self.EMAIL_REGEX, text):
            entity = Entity(
                entity="EMAIL",
                word=match.group(),
                start=match.start(),
                end=match.end(),
                score=1.0
            )
            entities.append(entity)

        # 키워드 주변 50자 내 이메일 찾기
        for keyword in self.KEYWORDS:
            for k_match in re.finditer(keyword, text, re.IGNORECASE):
                start_context = max(0, k_match.start() - 50)
                end_context = k_match.end() + 50
                context = text[start_context:end_context]

                for email_match in re.finditer(self.EMAIL_REGEX, context):
                    # 원본 텍스트 기준 start, end 계산
                    actual_start = start_context + email_match.start()
                    actual_end = start_context + email_match.end()

                    # word 기준 중복 제거
                    if not any(e.word == email_match.group() for e in entities):
                        entity = Entity(
                            entity="EMAIL",
                            word=email_match.group(),
                            start=actual_start,
                            end=actual_end,
                            score=1.0
                        )
                        entities.append(entity)

        return EntityGroup(entities)
