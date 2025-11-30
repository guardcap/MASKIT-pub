from app.utils.ner.korean_ner import KoreanNER 
from app.utils.entity import Entity, EntityGroup

class NerEngine:
    def __init__(self):
        print("...NEREngine 초기화 중...")
        self.korean_ner = KoreanNER()

    def ner_analyze(self, text: str) -> EntityGroup:
        raw_results = self.korean_ner.detect_korean_ner(text)
        entities = []

        for item in raw_results:
            entities.append(Entity(
                entity=item["entity_type"],     # PERSON, ORG, LOCATION
                score=item["score"],
                word=item["text"],
                start=item["start"],
                end=item["end"],
                pageIndex=None,
                bbox=None
            ))

        return EntityGroup(entities)
