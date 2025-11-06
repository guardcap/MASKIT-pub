import re
from typing import List
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

class IPRecognizer(EntityRecognizer):
    # IPv4, IPv6 정규식
    IPV4_REGEX = r"\b(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}\b"
    IPV6_REGEX = (
        r"(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|"
        r"([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|"
        r"([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|"
        r":((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|"
        r"::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}"
        r"(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:"
        r"((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"
    )

    KEYWORDS = ['ip주소', 'ip', '아이피', 'ip address']

    def __init__(self):
        super().__init__(name="ip_recognizer", supported_entities=["IP"])

    def analyze(self, text: str) -> EntityGroup:
        entities: List[Entity] = []

        # 전체 텍스트 스캔
        for regex in [self.IPV4_REGEX, self.IPV6_REGEX]:
            for match in re.finditer(regex, text, re.IGNORECASE):
                entities.append(Entity(
                    entity="IP",
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

                for regex in [self.IPV4_REGEX, self.IPV6_REGEX]:
                    for match in re.finditer(regex, context, re.IGNORECASE):
                        abs_start = start_context + match.start()
                        abs_end = start_context + match.end()

                        # 중복 제거: word + start 기준
                        if not any(e.word == match.group() and e.start == abs_start for e in entities):
                            entities.append(Entity(
                                entity="IP",
                                word=match.group(),
                                start=abs_start,
                                end=abs_end,
                                score=1.0
                            ))

        return EntityGroup(entities)
