import re
from typing import List
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

class ResidentIDRecognizer(EntityRecognizer):
    RESIDENT_ID_REGEX = r"\d{6}-\d{7}"
    KEYWORDS = ['주민등록번호', '주민번호', '신분증', '주민']

    def __init__(self):  
        super().__init__(name="residentid_recognizer", supported_entities=["RESIDENT_ID"])
        self.regex = re.compile(self.RESIDENT_ID_REGEX)

    def analyze(self, text: str) -> EntityGroup:
        entities: List[Entity] = []
        seen = set()  # (word, start) 기준 중복 제거

        # 전체 텍스트 스캔
        for match in self.regex.finditer(text):
            key = (match.group(), match.start())
            if key not in seen:
                entities.append(Entity(
                    entity="RESIDENT_ID",
                    word=match.group(),
                    start=match.start(),
                    end=match.end(),
                    score=1.0
                ))
                seen.add(key)

        # 키워드 주변 30자 내 스캔
        for keyword in self.KEYWORDS:
            for k_match in re.finditer(keyword, text, re.IGNORECASE):
                start_context = max(0, k_match.start() - 30)
                end_context = k_match.end() + 30
                context = text[start_context:end_context]

                for match in self.regex.finditer(context):
                    abs_start = start_context + match.start()
                    abs_end = start_context + match.end()
                    key = (match.group(), abs_start)
                    if key not in seen:
                        entities.append(Entity(
                            entity="RESIDENT_ID",
                            word=match.group(),
                            start=abs_start,
                            end=abs_end,
                            score=1.0
                        ))
                        seen.add(key)

        return EntityGroup(entities)
