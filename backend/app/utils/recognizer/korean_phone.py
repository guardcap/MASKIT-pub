import re
from typing import List
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

class PhoneRecognizer(EntityRecognizer):
    MOBILE_PHONE_REGEX = r"0(1[016789])[ \-]?\d{3,4}[ \-]?\d{4}"
    LOCAL_PHONE_REGEX = r"(?:(?:02|031|032|033|041|042|043|044|051|052|053|054|055|061|062|063|064)[ \-]?)?\d{3,4}[ \-]?\d{4}"
    INTERNATIONAL_PHONE_REGEX = r"(?:\+?82[ -]?)?(?:0)?(1[016789]|[2-6][0-9])[ -]?\d{3,4}[ -]?\d{4}"
    KEYWORDS = ['전화번호', '번호']

    def __init__(self):  
        super().__init__(name="phone_recognizer", supported_entities=["PHONE"])
        self.regexes = [re.compile(r) for r in [
            self.MOBILE_PHONE_REGEX, self.LOCAL_PHONE_REGEX, self.INTERNATIONAL_PHONE_REGEX
        ]]

    def analyze(self, text: str) -> EntityGroup:
        entities: List[Entity] = []

        # 중복 제거용 집합: (word, start) 기준
        seen = set()

        # 전체 텍스트 스캔
        for regex in self.regexes:
            for match in regex.finditer(text):
                cleaned_digits = re.sub(r"[^\d]", "", match.group())
                key = (match.group(), match.start())
                if 10 <= len(cleaned_digits) <= 13 and key not in seen:
                    entities.append(Entity(
                        entity="PHONE",
                        word=match.group(),
                        start=match.start(),
                        end=match.end(),
                        score=1.0
                    ))
                    seen.add(key)

        # 키워드 주변 50자 내 스캔
        for keyword in self.KEYWORDS:
            for k_match in re.finditer(keyword, text, re.IGNORECASE):
                start_context = max(0, k_match.start() - 50)
                end_context = k_match.end() + 50
                context = text[start_context:end_context]

                for regex in self.regexes:
                    for match in regex.finditer(context):
                        abs_start = start_context + match.start()
                        abs_end = start_context + match.end()
                        cleaned_digits = re.sub(r"[^\d]", "", match.group())
                        key = (match.group(), abs_start)
                        if 10 <= len(cleaned_digits) <= 13 and key not in seen:
                            entities.append(Entity(
                                entity="PHONE",
                                word=match.group(),
                                start=abs_start,
                                end=abs_end,
                                score=1.0
                            ))
                            seen.add(key)

        return EntityGroup(entities)
