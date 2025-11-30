import ollama

# 분석 대상 텍스트 (직접 주입)
input_text = """
정지옹은 4월 12일에 태어났고, 서울에 거주하고 있다. 그녀는 불교를 믿으며, 민주당을 지지한다.
마케팅 팀에서는 현재 삼성과의 협업을 진행하고자, 컨택을 시도할 예정이다.
김민호는 게이이며 지체장애 2등급이다. 
"""

# System 역할 프롬프트
system_prompt = """
너는 문서 내 민감 정보를 식별하는 보안 감사 전문가이다. 다음 기준에 따라 텍스트를 분석하라:

[민감 정보 기준]
1. 성적 지향, 정치 성향, 질병 기록, 가족 관계, 종교적 신념 등 개인의 민감한 속성
2. 사내 기밀 정보 (예: 기술 사양, 전략, 고객 정보, 미공개 계획 등)
3. 법적 분쟁 관련 정보 또는 계약 내용

[출력 형식]
1. 민감 정보 존재 여부: "예" 또는 "아니오"
2. 감지된 민감 정보 목록: 각 정보에 대해 내용과 유형을 간단히 기술
"""



# Ollama 호출 함수
def analyze_text_with_mistral(text: str):
    response = ollama.chat(
        model='mistral',
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"다음 텍스트에 민감 정보가 포함되어 있는가?\n\n{text}"}
        ]
    )
    return response['message']['content']

# 실행
if __name__ == "__main__":
    result = analyze_text_with_mistral(input_text)
    print("\n📊 민감 정보 탐지 결과:")
    print(result)
