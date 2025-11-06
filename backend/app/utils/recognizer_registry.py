from typing import Dict, List, Type
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

# 규칙 기반 인식기들 import
from app.utils.recognizer.email import EmailRecognizer
from app.utils.recognizer.gps import GPSRecognizer
from app.utils.recognizer.ipaddress import IPRecognizer
from app.utils.recognizer.korean_bank import BankAccountRecognizer
from app.utils.recognizer.korean_card import CardNumberRecognizer
from app.utils.recognizer.korean_drive import DriverLicenseRecognizer
from app.utils.recognizer.korean_passport import PassportRecognizer
from app.utils.recognizer.korean_phone import PhoneRecognizer
from app.utils.recognizer.korean_residentid import ResidentIDRecognizer
from app.utils.recognizer.MACaddress import MACRecognizer

class RecognizerRegistry:
    """모든 EntityRecognizer 객체들을 관리하고 로드"""

    def __init__(self):
        self.recognizers: Dict[str, EntityRecognizer] = {}

    def add_recognizer(self, recognizer: EntityRecognizer):
        if not isinstance(recognizer, EntityRecognizer):
            raise TypeError("추가하려는 객체는 EntityRecognizer의 인스턴스여야 합니다.")
        self.recognizers[recognizer.name] = recognizer

    def load_predefined_recognizers(self):
        predefined_recognizer_classes: List[Type[EntityRecognizer]] = [
            EmailRecognizer,
            GPSRecognizer,
            IPRecognizer,
            BankAccountRecognizer,
            CardNumberRecognizer,
            DriverLicenseRecognizer,
            PassportRecognizer,
            PhoneRecognizer,
            ResidentIDRecognizer,
            MACRecognizer
        ]
        for cls in predefined_recognizer_classes:
            self.add_recognizer(cls())

    def remove_recognizer(self, recognizer_name: str):
        if recognizer_name in self.recognizers:
            del self.recognizers[recognizer_name]
            print(f"인식기 '{recognizer_name}'가 제거되었습니다.")
        else:
            print(f"'{recognizer_name}'라는 이름의 인식기를 찾을 수 없습니다.")

    def regex_analyze(self, text: str) -> EntityGroup:
        """
        모든 규칙 기반 인식기를 실행하여 EntityGroup으로 통합.
        """
        merged = EntityGroup()
        for recognizer in self.recognizers.values():
            group = recognizer.analyze(text)  # 각 인식기의 EntityGroup
            merged = self._merge_groups(merged, group)
        return merged

    def get_supported_entities(self):
        supported = set()
        for r in self.recognizers.values():
            supported.update(r.supported_entities)
        return sorted(list(supported))

    @staticmethod
    def _merge_groups(a: EntityGroup, b: EntityGroup) -> EntityGroup:
        """
        엔티티 타입/범위 기준 중복을 간단히 제거하면서 병합.
        - 기본 정책: 동일 타입 & 겹치는 span은 더 긴 span 우선, 길이 같으면 score 높은 쪽 우선
        """
        if not a.entities:
            return EntityGroup(list(b.entities))
        if not b.entities:
            return EntityGroup(list(a.entities))

        result: List[Entity] = list(a.entities)

        def overlap(e1: Entity, e2: Entity) -> bool:
            return (e1.entity == e2.entity) and (e1.start < e2.end and e2.start < e1.end)

        for eb in b.entities:
            replaced = False
            for i, ea in enumerate(result):
                if overlap(ea, eb):
                    len_a = ea.end - ea.start
                    len_b = eb.end - eb.start
                    if len_b > len_a or (len_b == len_a and eb.score > ea.score):
                        result[i] = eb
                    replaced = True
                    break
            if not replaced:
                result.append(eb)

        # 정렬(시작 인덱스 기준)
        result.sort(key=lambda x: (x.start, x.end))
        return EntityGroup(result)
