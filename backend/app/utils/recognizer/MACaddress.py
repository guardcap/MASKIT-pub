import re
from typing import List
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

class MACRecognizer(EntityRecognizer):
    # 모든 형식의 MAC 주소 (콜론 또는 하이픈 구분자)
    MAC_REGEX = r"[0-9a-fA-F]{2}[:\-][0-9a-fA-F]{2}[:\-][0-9a-fA-F]{2}[:\-][0-9a-fA-F]{2}[:\-][0-9a-fA-F]{2}[:\-][0-9a-fA-F]{2}"
    KEYWORDS = ['mac주소', '맥주소', 'mac', '맥']

    def __init__(self):  
        super().__init__(name="MAC_recognizer", supported_entities=["MAC"])
        self.regex = re.compile(self.MAC_REGEX)
    
    def analyze(self, text: str) -> EntityGroup:
        entities: List[Entity] = []

        # 전체 텍스트 스캔
        for match in self.regex.finditer(text):
            if not any(e.start == match.start() and e.word == match.group() for e in entities):
                entities.append(Entity(
                    entity="MAC",
                    word=match.group(),
                    start=match.start(),
                    end=match.end(),
                    score=1.0
                ))

        # 키워드 주변 50자 내 스캔
        for keyword in self.KEYWORDS:
            for k_match in re.finditer(keyword, text, re.IGNORECASE):
                start_context = max(0, k_match.start() - 50)
                end_context = k_match.end() + 50
                context = text[start_context:end_context]

                for match in self.regex.finditer(context):
                    abs_start = start_context + match.start()
                    abs_end = start_context + match.end()
                    if not any(e.start == abs_start and e.word == match.group() for e in entities):
                        entities.append(Entity(
                            entity="MAC",
                            word=match.group(),
                            start=abs_start,
                            end=abs_end,
                            score=1.0
                        ))

        return EntityGroup(entities)
