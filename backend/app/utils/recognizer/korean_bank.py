import re
from typing import List
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

# backend/app/utils/recognizer/korean_bank.py

class BankAccountRecognizer(EntityRecognizer):
    # 계좌번호 정규식 - 하이픈 포함 패턴만 (더 정확함)
    ACCOUNT_PATTERNS = [
        r"\b\d{3}-\d{2,6}-\d{2,7}\b",     # 일반적인 계좌번호 패턴
        r"\b\d{4}-\d{2,6}-\d{2,7}\b",     # 4자리 시작
        r"\b\d{6}-\d{2}-\d{6}\b",         # 특정 은행 패턴
    ]

    # 제외 패턴
    EXCLUDE_PATTERNS = [
        r"(?:\d{4}-){3}\d{4}",            # 카드번호 (4-4-4-4)
        r"\d{6}-\d{7}",                   # 주민등록번호
        r"\d{2}-\d{2}-\d{6}-\d{2}",       # 운전면허번호
        r"01[016789]-?\d{3,4}-?\d{4}",    # 휴대폰
    ]

    KEYWORDS = ['계좌번호', '계좌', '통장', 'account', '은행', '입금', '송금']

    def __init__(self):
        super().__init__(name="bank_recognizer", supported_entities=["BANK_ACCOUNT"])
        self.account_regexes = [re.compile(p) for p in self.ACCOUNT_PATTERNS]
        self.exclude_regex = re.compile("|".join(self.EXCLUDE_PATTERNS))
        self.keyword_regexes = [re.compile(k, re.IGNORECASE) for k in self.KEYWORDS]

    def valid_account(self, account: str) -> bool:
        """계좌번호로 유효한지 검증"""
        # 제외 패턴 체크
        if self.exclude_regex.search(account):
            print(f"[계좌번호 검증] 제외 패턴 매칭: {account}")
            return False
        
        # 하이픈이 없으면 제외 (하이픈 필수)
        if '-' not in account:
            print(f"[계좌번호 검증] 하이픈 없음: {account}")
            return False
        
        # 숫자만 추출
        digits = re.sub(r"\D", "", account)
        
        # 길이 검증 (10~16자리)
        if not (10 <= len(digits) <= 16):
            print(f"[계좌번호 검증] 길이 오류 ({len(digits)}자리): {account}")
            return False
        
        # 13자리는 주민번호 가능성
        if len(digits) == 13:
            month = int(digits[2:4])
            day = int(digits[4:6])
            gender_code = int(digits[6])
            if (1 <= month <= 12 and 1 <= day <= 31 and 1 <= gender_code <= 8):
                print(f"[계좌번호 검증] 주민번호 패턴: {account}")
                return False
        
        # 12자리도 주민번호 일부일 수 있음
        if len(digits) == 12:
            month = int(digits[2:4])
            day = int(digits[4:6])
            if 1 <= month <= 12 and 1 <= day <= 31:
                print(f"[계좌번호 검증] 주민번호 일부 가능성: {account}")
                return False
        
        # 11자리도 의심 (주민번호에서 한 자리 빠진 경우)
        if len(digits) == 11:
            month = int(digits[2:4])
            day = int(digits[4:6])
            if 1 <= month <= 12 and 1 <= day <= 31:
                print(f"[계좌번호 검증] 주민번호 관련 의심: {account}")
                return False
        
        # 전화번호 패턴
        if digits.startswith(('010', '011', '016', '017', '018', '019', 
                             '02', '031', '032', '033', '041', '042', '043', '044',
                             '051', '052', '053', '054', '055', '061', '062', '063', '064')):
            print(f"[계좌번호 검증] 전화번호 패턴: {account}")
            return False
        
        return True

    def analyze(self, text: str) -> EntityGroup:
        entities: List[Entity] = []
        seen = set()

        # 키워드 주변에서만 검색 (더 정확함)
        for kw_re in self.keyword_regexes:
            for k_match in kw_re.finditer(text):
                start_context = max(0, k_match.start() - 10)
                end_context = k_match.end() + 60
                context = text[start_context:end_context]

                for regex in self.account_regexes:
                    for match in regex.finditer(context):
                        acc = match.group()
                        if not self.valid_account(acc):
                            continue
                        
                        abs_start = start_context + match.start()
                        abs_end = start_context + match.end()
                        
                        key = (acc, abs_start)
                        if key not in seen:
                            entities.append(Entity(
                                entity="BANK_ACCOUNT",
                                word=acc,
                                start=abs_start,
                                end=abs_end,
                                score=1.0
                            ))
                            seen.add(key)
                            print(f"[계좌번호] 발견: {acc} at {abs_start}")

        return EntityGroup(entities)