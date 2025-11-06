import re
from typing import List
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

class GPSRecognizer(EntityRecognizer):
    """
    다양한 형식의 GPS 좌표(위도, 경도)를 인식하도록 확장된 클래스입니다.
    """
    # '위도, 경도' 형식 정규식
    PAIR_REGEX = r"\b([+-]?\d{1,2}\.\d+)[,\s]+([+-]?\d{1,3}\.\d+)\b"
    
    # '위도: ~', '경도: ~' 형식 정규식
    KEY_VALUE_REGEX = r"(?:위도|경도|latitude|longitude|lat|lon)\s*:\s*([+-]?\d{1,3}\.\d+)"
    
    KEYWORDS = ['위치', 'gps', '위도', '경도', '좌표']

    def __init__(self):
        super().__init__(name="gps_recognizer", supported_entities=["GPS"])

    def analyze(self, text: str) -> EntityGroup:
        """
        주어진 텍스트에서 GPS 좌표를 분석하고 EntityGroup으로 반환
        """
        entities = []

        # 전체 텍스트 스캔: '위도, 경도' 쌍
        for match in re.finditer(self.PAIR_REGEX, text):
            lat, lon = match.groups()
            # 위도
            entities.append(Entity(
                entity="GPS",
                word=lat,
                start=match.start(1),
                end=match.end(1),
                score=1.0
            ))
            # 경도
            entities.append(Entity(
                entity="GPS",
                word=lon,
                start=match.start(2),
                end=match.end(2),
                score=1.0
            ))

        # 전체 텍스트 스캔: '위도: ~', '경도: ~' 형식
        for match in re.finditer(self.KEY_VALUE_REGEX, text, re.IGNORECASE):
            value = match.group(1)
            entities.append(Entity(
                entity="GPS",
                word=value,
                start=match.start(1),
                end=match.end(1),
                score=1.0
            ))

        # 키워드 주변 50자 내 추가 탐지
        for keyword in self.KEYWORDS:
            for k_match in re.finditer(keyword, text, re.IGNORECASE):
                start_context = max(0, k_match.start() - 50)
                end_context = k_match.end() + 50
                context = text[start_context:end_context]

                # '위도, 경도' 쌍
                for match in re.finditer(self.PAIR_REGEX, context):
                    lat, lon = match.groups()
                    actual_start_lat = start_context + match.start(1)
                    actual_end_lat = start_context + match.end(1)
                    actual_start_lon = start_context + match.start(2)
                    actual_end_lon = start_context + match.end(2)

                    # 중복 제거: word+start 기준
                    if not any(e.word == lat and e.start == actual_start_lat for e in entities):
                        entities.append(Entity(
                            entity="GPS",
                            word=lat,
                            start=actual_start_lat,
                            end=actual_end_lat,
                            score=1.0
                        ))
                    if not any(e.word == lon and e.start == actual_start_lon for e in entities):
                        entities.append(Entity(
                            entity="GPS",
                            word=lon,
                            start=actual_start_lon,
                            end=actual_end_lon,
                            score=1.0
                        ))

                # '위도: ~', '경도: ~' 형식
                for match in re.finditer(self.KEY_VALUE_REGEX, context, re.IGNORECASE):
                    value = match.group(1)
                    actual_start = start_context + match.start(1)
                    actual_end = start_context + match.end(1)
                    if not any(e.word == value and e.start == actual_start for e in entities):
                        entities.append(Entity(
                            entity="GPS",
                            word=value,
                            start=actual_start,
                            end=actual_end,
                            score=1.0
                        ))

        return EntityGroup(entities)
