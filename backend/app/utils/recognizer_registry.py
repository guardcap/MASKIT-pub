from typing import Dict, List, Type
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup
import re

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


class DynamicRegexRecognizer(EntityRecognizer):
    """MongoDB의 커스텀 엔티티를 위한 동적 Recognizer"""

    def __init__(self, entity_id: str, entity_type: str, name: str, regex_pattern: str = None, keywords: List[str] = None):
        super().__init__(name=f"dynamic_{entity_id}", supported_entities=[entity_type])
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.display_name = name
        self.regex_pattern = regex_pattern
        self.keywords = keywords or []

    def analyze(self, text: str) -> EntityGroup:
        entities: List[Entity] = []

        # Regex 패턴이 있으면 사용
        if self.regex_pattern:
            try:
                for match in re.finditer(self.regex_pattern, text, re.IGNORECASE):
                    entities.append(Entity(
                        entity=self.entity_type,
                        word=match.group(),
                        start=match.start(),
                        end=match.end(),
                        score=1.0
                    ))
            except Exception as e:
                print(f"Regex 오류 ({self.entity_id}): {e}")

        # 키워드 주변 스캔
        if self.regex_pattern and self.keywords:
            for keyword in self.keywords:
                for k_match in re.finditer(keyword, text, re.IGNORECASE):
                    start_context = max(0, k_match.start() - 50)
                    end_context = k_match.end() + 50
                    context = text[start_context:end_context]

                    try:
                        for match in re.finditer(self.regex_pattern, context, re.IGNORECASE):
                            abs_start = start_context + match.start()
                            abs_end = start_context + match.end()

                            # 중복 제거
                            if not any(e.word == match.group() and e.start == abs_start for e in entities):
                                entities.append(Entity(
                                    entity=self.entity_type,
                                    word=match.group(),
                                    start=abs_start,
                                    end=abs_end,
                                    score=1.0
                                ))
                    except Exception as e:
                        print(f"Keyword Regex 오류 ({self.entity_id}): {e}")

        return EntityGroup(entities)


class RecognizerRegistry:
    """모든 EntityRecognizer 객체들을 관리하고 로드"""

    def __init__(self, db_client=None):
        self.recognizers: Dict[str, EntityRecognizer] = {}
        self.db_client = db_client

        # 엔티티 우선순위 정의
        self.entity_priority = {
            'RESIDENT_ID': 1,      # 최우선 (주민번호)
            'PHONE': 2,            # 전화번호
            'CARD_NUMBER': 3,      # 카드번호
            'PASSPORT': 4,         # 여권번호
            'DRIVE': 5,            # 운전면허
            'BANK_ACCOUNT': 6,     # 계좌번호 (가장 낮은 우선순위)
        }

        
    def add_recognizer(self, recognizer: EntityRecognizer):
        if not isinstance(recognizer, EntityRecognizer):
            raise TypeError("추가하려는 객체는 EntityRecognizer의 인스턴스여야 합니다.")
        self.recognizers[recognizer.name] = recognizer

    def load_predefined_recognizers(self):
        """기본 제공 Recognizer 로드"""
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

    async def load_custom_recognizers(self):
        """MongoDB의 커스텀 엔티티를 동적 Recognizer로 로드"""
        if self.db_client is None:
            print("⚠️  DB 클라이언트가 없어 커스텀 엔티티를 로드할 수 없습니다.")
            return

        try:
            # MongoDB에서 활성화된 커스텀 엔티티 조회
            cursor = self.db_client["entities"].find({"is_active": True})
            custom_count = 0

            async for entity_doc in cursor:
                entity_id = entity_doc.get("entity_id")
                name = entity_doc.get("name")
                entity_type = entity_doc.get("entity_id", "CUSTOM").upper()
                regex_pattern = entity_doc.get("regex_pattern")
                keywords = entity_doc.get("keywords", [])

                # 키워드가 문자열인 경우 리스트로 변환
                if isinstance(keywords, str):
                    keywords = [kw.strip() for kw in keywords.split(',') if kw.strip()]

                # 동적 Recognizer 생성 및 추가
                if regex_pattern:  # Regex가 있는 경우만 추가
                    recognizer = DynamicRegexRecognizer(
                        entity_id=entity_id,
                        entity_type=entity_type,
                        name=name,
                        regex_pattern=regex_pattern,
                        keywords=keywords
                    )
                    self.add_recognizer(recognizer)
                    custom_count += 1
                    print(f"✅ 커스텀 엔티티 로드: {name} ({entity_type})")

            print(f"📦 총 {custom_count}개의 커스텀 엔티티가 로드되었습니다.")

        except Exception as e:
            print(f"❌ 커스텀 엔티티 로드 실패: {e}")

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


    def _remove_overlapping_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        겹치는 엔티티 제거 (우선순위 기반)
        
        우선순위:
        1. RESIDENT_ID (주민번호) - 최우선
        2. PHONE (전화번호)
        3. CARD_NUMBER (카드번호)
        4. PASSPORT (여권번호)
        5. DRIVE (운전면허)
        6. BANK_ACCOUNT (계좌번호) - 최저 우선순위
        """
        if not entities:
            return []
        
        # 시작 위치, 길이 순으로 정렬 (긴 것이 먼저)
        sorted_entities = sorted(entities, key=lambda x: (x.start, -(x.end - x.start)))
        
        result: List[Entity] = []
        
        for current in sorted_entities:
            should_add = True
            entities_to_remove = []
            
            for i, existing in enumerate(result):
                # 겹침 유형 판단
                overlap_type = self._get_overlap_type(current, existing)
                
                if overlap_type == "none":
                    continue
                
                # 우선순위 비교
                current_priority = self.entity_priority.get(current.entity, 999)
                existing_priority = self.entity_priority.get(existing.entity, 999)
                current_len = current.end - current.start
                existing_len = existing.end - existing.start
                
                # ===== 부분 겹침 처리 (핵심) =====
                if overlap_type in ["partial", "current_contains_existing", "existing_contains_current"]:
                    # 우선순위가 높은 것 선택
                    if current_priority < existing_priority:
                        entities_to_remove.append(i)
                        print(f"[겹침 제거] {existing.entity} '{existing.word}'[{existing.start}:{existing.end}] 제거 "
                            f"← 우선순위: {current.entity} '{current.word}'[{current.start}:{current.end}]")
                    elif current_priority > existing_priority:
                        should_add = False
                        print(f"[겹침 제거] {current.entity} '{current.word}'[{current.start}:{current.end}] 스킵 "
                            f"← 우선순위: {existing.entity}")
                        break
                    else:
                        # 우선순위 같으면 더 긴 것 선택
                        if current_len > existing_len:
                            entities_to_remove.append(i)
                            print(f"[겹침 제거] {existing.entity} '{existing.word}' 제거 ← 길이")
                        else:
                            should_add = False
                            print(f"[겹침 제거] {current.entity} '{current.word}' 스킵 ← 길이")
                            break
                
                # ===== 동일 시작 위치 처리 =====
                elif overlap_type == "same_start":
                    if current_priority < existing_priority:
                        entities_to_remove.append(i)
                    elif current_priority > existing_priority:
                        should_add = False
                        break
                    else:
                        if current_len > existing_len:
                            entities_to_remove.append(i)
                        else:
                            should_add = False
                            break
            
            # 제거할 엔티티 삭제 (역순)
            for idx in sorted(entities_to_remove, reverse=True):
                result.pop(idx)
            
            if should_add:
                result.append(current)
        
        # 최종 정렬 (시작 위치 순)
        result.sort(key=lambda x: (x.start, x.end))
        return result


    @staticmethod
    def _get_overlap_type(e1: Entity, e2: Entity) -> str:
        """
        두 엔티티의 겹침 유형 반환
        """
        # 겹치지 않음
        if e1.end <= e2.start or e2.end <= e1.start:
            return "none"
        
        # e1이 e2를 완전히 포함
        if e1.start <= e2.start and e1.end >= e2.end:
            if e1.start == e2.start and e1.end == e2.end:
                return "same_start"
            return "current_contains_existing"
        
        # e2가 e1을 완전히 포함
        if e2.start <= e1.start and e2.end >= e1.end:
            if e1.start == e2.start:
                return "same_start"
            return "existing_contains_current"
        
        # 시작 위치가 같음
        if e1.start == e2.start:
            return "same_start"
        
        # 부분 겹침 (핵심: 이 케이스가 02-123-4567과 123-4567 같은 경우)
        return "partial"