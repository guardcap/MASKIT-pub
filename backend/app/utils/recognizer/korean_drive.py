import re
from typing import List
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

class DriverLicenseRecognizer(EntityRecognizer):
    # 예: 11-01-123456-78
    DRIVER_LICENSE_REGEX = r"\d{2}-\d{2}-\d{6}-\d{2}"
    KEYWORDS = ['운전면허', '면허번호', '운전']

    def __init__(self):  
        super().__init__(name="driverlicense_recognizer", supported_entities=["DRIVE"])

    def analyze(self, text: str) -> EntityGroup:
        entities: List[Entity] = []

        # 전체 텍스트에서 운전면허번호 추출
        for match in re.finditer(self.DRIVER_LICENSE_REGEX, text):
            entity = Entity(
                entity="DRIVE",
                word=match.group(),
                start=match.start(),
                end=match.end(),
                score=1.0
            )
            entities.append(entity)

        # 키워드 주변 50자 내에서 운전면허번호 추출
        for keyword in self.KEYWORDS:
            for k_match in re.finditer(keyword, text, re.IGNORECASE):
                start_context = max(0, k_match.start() - 50)
                end_context = k_match.end() + 50
                context = text[start_context:end_context]

                for match in re.finditer(self.DRIVER_LICENSE_REGEX, context):
                    abs_start = start_context + match.start()
                    abs_end = start_context + match.end()
                    # 중복 제거: word + start 기준
                    if not any(e.word == match.group() and e.start == abs_start for e in entities):
                        entities.append(Entity(
                            entity="DRIVE",
                            word=match.group(),
                            start=abs_start,
                            end=abs_end,
                            score=1.0
                        ))

        return EntityGroup(entities)
