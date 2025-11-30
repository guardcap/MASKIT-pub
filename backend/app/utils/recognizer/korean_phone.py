import re
from typing import List
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

# backend/app/utils/recognizer/korean_phone.py

class PhoneRecognizer(EntityRecognizer):
    # 더 엄격한 패턴으로 수정
    MOBILE_PHONE_REGEX = r"\b0(1[016789])[ \-]?\d{3,4}[ \-]?\d{4}\b"
    
    # 지역번호는 반드시 02 또는 0XX 형식
    LOCAL_PHONE_REGEX = r"\b(02|0[3-6][1-4])[ \-]?\d{3,4}[ \-]?\d{4}\b"
    
    KEYWORDS = ['전화번호', '번호', '연락처', '휴대폰', '핸드폰', '전화', 'tel', 'phone']

    def __init__(self):  
        super().__init__(name="phone_recognizer", supported_entities=["PHONE"])
        self.mobile_regex = re.compile(self.MOBILE_PHONE_REGEX)
        self.local_regex = re.compile(self.LOCAL_PHONE_REGEX)

    def is_valid_phone(self, text: str) -> bool:
        """전화번호로 유효한지 검증"""
        # 숫자만 추출
        digits = re.sub(r'[^\d]', '', text)
        
        # 길이 체크 (9~11자리만 허용)
        if not (9 <= len(digits) <= 11):
            print(f"[전화번호 검증] 길이 오류 ({len(digits)}자리): {text}")
            return False
        
        # 휴대폰 번호 패턴 (010, 011, 016, 017, 018, 019로 시작, 10-11자리)
        if re.match(r'^01[016789]\d{7,8}$', digits):
            return True
        
        # 지역번호 패턴 (02는 9-10자리, 나머지는 10-11자리)
        if digits.startswith('02'):
            if len(digits) in [9, 10]:
                return True
        elif re.match(r'^0[3-6][1-4]', digits):
            if len(digits) in [10, 11]:
                return True
        
        print(f"[전화번호 검증] 패턴 불일치: {text}")
        return False

    def analyze(self, text: str) -> EntityGroup:
        entities: List[Entity] = []
        seen = set()

        # 휴대폰 번호 스캔
        for match in self.mobile_regex.finditer(text):
            phone_number = match.group()
            
            if not self.is_valid_phone(phone_number):
                continue
            
            key = (phone_number, match.start())
            if key not in seen:
                entities.append(Entity(
                    entity="PHONE",
                    word=phone_number,
                    start=match.start(),
                    end=match.end(),
                    score=1.0
                ))
                seen.add(key)
                print(f"[전화번호] 발견: {phone_number} at {match.start()}")

        # 지역번호 스캔
        for match in self.local_regex.finditer(text):
            phone_number = match.group()
            
            if not self.is_valid_phone(phone_number):
                continue
            
            key = (phone_number, match.start())
            if key not in seen:
                entities.append(Entity(
                    entity="PHONE",
                    word=phone_number,
                    start=match.start(),
                    end=match.end(),
                    score=1.0
                ))
                seen.add(key)
                print(f"[전화번호] 발견: {phone_number} at {match.start()}")

        # 키워드 주변 스캔
        for keyword in self.KEYWORDS:
            for k_match in re.finditer(keyword, text, re.IGNORECASE):
                start_context = max(0, k_match.start() - 10)
                end_context = k_match.end() + 50
                context = text[start_context:end_context]

                for regex in [self.mobile_regex, self.local_regex]:
                    for match in regex.finditer(context):
                        abs_start = start_context + match.start()
                        abs_end = start_context + match.end()
                        phone_number = match.group()
                        
                        if not self.is_valid_phone(phone_number):
                            continue
                        
                        key = (phone_number, abs_start)
                        if key not in seen:
                            entities.append(Entity(
                                entity="PHONE",
                                word=phone_number,
                                start=abs_start,
                                end=abs_end,
                                score=1.0
                            ))
                            seen.add(key)

        return EntityGroup(entities)