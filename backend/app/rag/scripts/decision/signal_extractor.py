import re

class SignalExtractor:
    """
    문서 텍스트에서 DANGER, WARN, SAFE 신호를 추출하는 클래스.
    신호는 DANGER > WARN > SAFE 순으로 우선순위를 갖는다.
    """
    
    # 각 신호에 해당하는 키워드 또는 정규식 패턴 정의
    # 프로젝트에 맞게 키워드를 구체적으로 추가하거나 수정하세요.
    DANGER_KEYWORDS = [
        "금지", "불가", "불가능", "절대 안됨", "엄금", "유출", "위반",
        "삭제해야", "파기해야", "삭제 필수", "파기 필수"
    ]
    WARN_KEYWORDS = [
        "주의", "경고", "제한적", "부분 허용", "예외적으로", "신중하게",
        "~하는 경우에만", "~제외", "마스킹", "비식별화", "일부 공개"
    ]
    SAFE_KEYWORDS = [
        "허용", "가능", "권장", "문제 없음", "공개 가능", "제공 가능",
        "필수 제공", "필수 수집"
    ]

    def __init__(self):
        # 성능을 위해 정규식 패턴을 미리 컴파일
        self.patterns = {
            "DANGER": re.compile('|'.join(self.DANGER_KEYWORDS), re.IGNORECASE),
            "WARN": re.compile('|'.join(self.WARN_KEYWORDS), re.IGNORECASE),
            "SAFE": re.compile('|'.join(self.SAFE_KEYWORDS), re.IGNORECASE),
        }

    def extract_signal(self, text: str) -> str:
        """
        주어진 텍스트에서 가장 높은 우선순위의 신호를 추출한다.
        
        Args:
            text (str): 분석할 문서의 텍스트.

        Returns:
            str: "DANGER", "WARN", "SAFE" 중 하나 또는 "NONE".
        """
        if not isinstance(text, str):
            return "NONE"

        # 우선순위가 높은 DANGER 신호부터 확인
        if self.patterns["DANGER"].search(text):
            return "DANGER"
        
        # 다음으로 WARN 신호 확인
        if self.patterns["WARN"].search(text):
            return "WARN"
            
        # 마지막으로 SAFE 신호 확인
        if self.patterns["SAFE"].search(text):
            return "SAFE"
            
        # 아무 키워드도 발견되지 않으면 NONE 반환
        return "NONE"

# --- 사용 예시 ---
if __name__ == '__main__':
    extractor = SignalExtractor()

    # 테스트할 문서 예시
    doc_a = "개인정보 제3자 제공은 원칙적으로 금지됩니다."
    doc_b = "사내 공지 시, 담당자 연락처는 마스킹 처리 후 공개해야 합니다. 주의하세요."
    doc_c = "업무에 필요한 최소한의 개인정보 수집은 허용됩니다."
    doc_d = "오늘의 날씨는 맑음입니다."

    print(f"문서 A: \"{doc_a}\"")
    print(f"  -> 추출된 신호: {extractor.extract_signal(doc_a)}\n") # 예상 결과: DANGER

    print(f"문서 B: \"{doc_b}\"")
    print(f"  -> 추출된 신호: {extractor.extract_signal(doc_b)}\n") # 예상 결과: WARN

    print(f"문서 C: \"{doc_c}\"")
    print(f"  -> 추출된 신호: {extractor.extract_signal(doc_c)}\n") # 예상 결과: SAFE
    
    print(f"문서 D: \"{doc_d}\"")
    print(f"  -> 추출된 신호: {extractor.extract_signal(doc_d)}\n") # 예상 결과: NONE