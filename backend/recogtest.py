# backend/test_substring.py
from app.utils.recognizer_registry import RecognizerRegistry

registry = RecognizerRegistry()
registry.load_predefined_recognizers()

test_cases = [
    """계좌 번호
800101-223456
주민등록번호
800101-2234567""",
    "주민번호: 880101-1234567",
    "계좌: 288-910581-91007",
    "800101-2234567 이 사람의 계좌는 28891058191007",
]

for text in test_cases:
    print(f"\n{'='*60}")
    print(f"입력:\n{text}")
    print(f"{'-'*60}")
    result = registry.regex_analyze(text)
    if result.entities:
        for entity in result.entities:
            print(f"  ✓ {entity.entity:15s} | '{entity.word}' | 위치: {entity.start}-{entity.end}")
    else:
        print("  (PII 없음)")
