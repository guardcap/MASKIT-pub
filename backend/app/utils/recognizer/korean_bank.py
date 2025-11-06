import re
from typing import List
from app.utils.entity_recognizer import EntityRecognizer
from app.utils.entity import Entity, EntityGroup

class BankAccountRecognizer(EntityRecognizer):
    # 계좌번호 정규식 리스트
    ACCOUNT_PATTERNS = [
        r"\d{3}-?\d{2}\d{1}\d{3}-?\d{3}",
        r"\d{6}-?\d{2}-?\d{6}",
        r"\d{3}-?\d{3}\d{3}-?\d{2}-?\d{3}",
        r"\d{3}-?\d{3}\d{1}-?\d{4}-?\d{2}",
        r"\d{3}-?\d{3}-?\d{6}",
        r"\d{4}-?\d{2}\d{1}-?\d{6}",
        r"\d{3}-?\d{3}\d{3}-?\d{5}",
        r"\d{3}-?\d{3}\d{3}-?\d{3}",
        r"\d{3}-?\d{2}-?\d{1}\d{5}-?\d{1}",
        r"\d{3}-?\d{3}\d{1}-?\d{4}-?\d{2}",
        r"\d{3}-?\d{2}-?\d{1}\d{5}",
        r"\d{4}-?\d{2}-?\d{7}",
        r"\b\d{10,16}\b",
    ]

    # 제외 패턴 (카드번호, 주민번호, 휴대폰 등)
    EXCLUDE_PATTERNS = [
        r"(?:\d{4}-){3}\d{4}",     # 카드번호 (4-4-4-4)
        r"\d{6}-\d{7}",            # 주민등록번호
        r"\d{2}-\d{2}-\d{6}-\d{2}", # 운전면허번호
        r"010-\d{4}-\d{4}",        # 휴대폰번호
    ]

    KEYWORDS = ['계좌번호', '계좌', '통장', 'account', '은행']

    def __init__(self):
        super().__init__(name="bank_recognizer", supported_entities=["BANK_ACCOUNT"])
        self.account_regexes = [re.compile(p) for p in self.ACCOUNT_PATTERNS]
        self.exclude_regex = re.compile("|".join(self.EXCLUDE_PATTERNS))
        self.keyword_regexes = [re.compile(k, re.IGNORECASE) for k in self.KEYWORDS]

    def valid_account(self, account: str) -> bool:
        if self.exclude_regex.search(account):
            return False
        digits = re.sub(r"\D", "", account)
        return 10 <= len(digits) <= 16

    def analyze(self, text: str) -> EntityGroup:
        entities: List[Entity] = []

        # 전체 텍스트 스캔
        for regex in self.account_regexes:
            for match in regex.finditer(text):
                acc = match.group()
                if not self.valid_account(acc):
                    continue
                start, end = match.start(), match.end()
                
                # 중복 제거: 범위 겹치면 skip
                if any(e.start < end and start < e.end for e in entities):
                    continue

                entities.append(Entity(
                    entity="BANK_ACCOUNT",
                    word=acc,
                    start=start,
                    end=end,
                    score=1.0
                ))

        # 키워드 주변 30~60자 내 스캔
        for kw_re in self.keyword_regexes:
            for k_match in kw_re.finditer(text):
                start_context = max(0, k_match.start() - 30)
                end_context = k_match.end() + 60
                context = text[start_context:end_context]

                for regex in self.account_regexes:
                    for match in regex.finditer(context):
                        acc = match.group()
                        if not self.valid_account(acc):
                            continue
                        abs_start = start_context + match.start()
                        abs_end = start_context + match.end()

                        # 중복 제거: 범위 겹치면 skip
                        if any(e.start < abs_end and abs_start < e.end for e in entities):
                            continue

                        entities.append(Entity(
                            entity="BANK_ACCOUNT",
                            word=acc,
                            start=abs_start,
                            end=abs_end,
                            score=1.0
                        ))

        return EntityGroup(entities)
