import re
from typing import List
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

class ResidentIDRecognizer(EntityRecognizer):
    RESIDENT_ID_REGEX = r"\d{6}[ \-]?\d{7}"
    KEYWORDS = ['주민등록번호', '주민번호', '신분증', '주민', '생년월일']

    def __init__(self):  
        super().__init__(name="residentid_recognizer", supported_entities=["RESIDENT_ID"])
        self.regex = re.compile(self.RESIDENT_ID_REGEX)

    def is_valid_resident_id(self, text: str) -> bool:
        """주민번호로 유효한지 검증"""
        # 숫자만 추출
        digits = re.sub(r'[^\d]', '', text)
        
        # 정확히 13자리
        if len(digits) != 13:
            return False
        
        # 앞 6자리: 생년월일 검증
        year = int(digits[0:2])
        month = int(digits[2:4])
        day = int(digits[4:6])
        
        # 월 검증 (1~12)
        if not (1 <= month <= 12):
            return False
        
        # 일 검증 (1~31)
        if not (1 <= day <= 31):
            return False
        
        # 뒷자리 첫 번호: 성별 코드 (1~4, 5~8)
        gender_code = int(digits[6])
        if gender_code not in [1, 2, 3, 4, 5, 6, 7, 8]:
            return False
        
        # 전화번호 패턴이면 제외 (010으로 시작하면)
        if digits.startswith('010') or digits.startswith('011'):
            return False
        
        return True

    def analyze(self, text: str) -> EntityGroup:
        entities: List[Entity] = []
        seen = set()

        # 전체 텍스트 스캔
        for match in self.regex.finditer(text):
            resident_id = match.group()
            
            # 유효성 검증
            if not self.is_valid_resident_id(resident_id):
                continue
            
            key = (resident_id, match.start())
            if key not in seen:
                entities.append(Entity(
                    entity="RESIDENT_ID",
                    word=resident_id,
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
                    resident_id = match.group()
                    
                    # 유효성 검증
                    if not self.is_valid_resident_id(resident_id):
                        continue
                    
                    key = (resident_id, abs_start)
                    if key not in seen:
                        entities.append(Entity(
                            entity="RESIDENT_ID",
                            word=resident_id,
                            start=abs_start,
                            end=abs_end,
                            score=1.0
                        ))
                        seen.add(key)

        return EntityGroup(entities)