import json

# --- 결정 엔진 임계치 설정 (향후 테스트를 통해 튜닝 필요) ---

# DANGER 점수 총합이 이 값을 넘으면 무조건 'DANGER'로 결정
DANGER_THRESHOLD = 1.5

# DANGER와 SAFE 점수 차이가 이 값보다 작으면 'WARN', 크거나 같으면 'SAFE'로 결정
SCORE_GAP_THRESHOLD = 0.8

class DecisionEngine:
    """
    검색된 근거(A, B, C)와 점수를 바탕으로 최종 마스킹 여부를 결정하는 클래스.
    """
    def __init__(self):
        # 임계값들을 클래스 속성으로 저장
        self.danger_threshold = DANGER_THRESHOLD
        self.score_gap_threshold = SCORE_GAP_THRESHOLD
        print("✅ 결정 엔진 초기화 완료")
        print(f"   - 위험도(DANGER) 임계치: {self.danger_threshold}")
        print(f"   - 점수 격차(GAP) 임계치: {self.score_gap_threshold}")

    def make_decision(self, danger_score: float, safe_score: float, a_case_results: list) -> dict:
        """
        입력된 점수와 사례를 바탕으로 결정 로직을 순차적으로 적용하여 최종 결과를 반환합니다.

        :param danger_score: B(규정), C(법률) 검색 결과의 DANGER 지수 총합
        :param safe_score: B(규정), C(법률) 검색 결과의 SAFE 지수 총합
        :param a_case_results: A(사례) 검색 결과 상위 3개 리스트
        :return: 결정 결과 딕셔너리
        """
        
        # 규칙 1: DANGER 지수가 임계치 이상이면 무조건 'DANGER'
        if danger_score >= self.danger_threshold:
            return {
                'decision': 'DANGER',
                'reason': f'위험도 점수({danger_score:.2f})가 임계치({self.danger_threshold}) 이상으로, 전체 마스킹이 필요합니다.',
                'action': {'type': 'full_mask'}
            }

        # 규칙 2: A(사례) 상위 3개의 처리 결과(after_text)가 모두 동일하면 'WARN'
        if len(a_case_results) == 3:
            # meta 필드가 없는 경우를 대비하여 .get() 사용
            after_texts = [res.get('meta', {}).get('after_text') for res in a_case_results]
            # None이 아니고, 모든 요소가 첫 번째 요소와 동일한지 확인
            if after_texts[0] is not None and all(t == after_texts[0] for t in after_texts):
                return {
                    'decision': 'WARN',
                    'reason': '과거 처리 사례 Top 3의 마스킹 방식이 모두 동일하여, 일관된 규칙을 적용합니다.',
                    'action': {'type': 'partial_mask', 'suggestion': after_texts[0]}
                }

        # 규칙 3: DANGER, SAFE 점수 격차가 크지 않다면 모호한 상황으로 보고 'WARN'
        if abs(safe_score - danger_score) < self.score_gap_threshold:
            suggestion = "가장 유사한 과거 사례 없음"
            if a_case_results:
                suggestion = a_case_results[0].get('meta', {}).get('after_text', suggestion)
            
            return {
                'decision': 'WARN',
                'reason': f'안전도({safe_score:.2f})와 위험도({danger_score:.2f}) 점수 차이가 임계치({self.score_gap_threshold}) 미만으로 판단이 모호합니다. 가장 유사한 사례를 따릅니다.',
                'action': {'type': 'partial_mask', 'suggestion': suggestion}
            }
        
        # 규칙 4: 위 모든 조건에 해당하지 않고, SAFE 점수가 충분히 높다면 'SAFE'
        # (safe_score - danger_score >= self.score_gap_threshold 인 경우)
        return {
            'decision': 'SAFE',
            'reason': f'안전도 점수({safe_score:.2f})가 위험도 점수({danger_score:.2f})보다 충분히 높아 안전한 것으로 판단됩니다.',
            'action': {'type': 'no_mask'}
        }

# --- 사용 예시 및 테스트 ---
if __name__ == '__main__':
    engine = DecisionEngine()
    print("\n--- 결정 엔진 시나리오 테스트 ---")

    # 테스트용 모의(mock) 데이터
    mock_cases = [
        {'meta': {'after_text': '주소는 OOO으로 마스킹'}},
        {'meta': {'after_text': '주소는 OOO으로 마스킹'}},
        {'meta': {'after_text': '주소는 OOO으로 마스킹'}}
    ]
    mock_cases_different = [
        {'meta': {'after_text': '주소는 OOO으로 마스킹'}},
        {'meta': {'after_text': '좌표 정보 삭제'}},
        {'meta': {'after_text': '주소 비공개 처리'}}
    ]

    # 시나리오 1: 위험도가 매우 높은 경우
    print("\n[1] 위험도가 임계치를 넘는 경우 (DANGER)")
    decision_1 = engine.make_decision(danger_score=2.1, safe_score=0.5, a_case_results=mock_cases_different)
    print(json.dumps(decision_1, indent=2, ensure_ascii=False))

    # 시나리오 2: 위험도는 낮지만, 과거 사례 3개가 모두 일치하는 경우
    print("\n[2] 과거 사례 3개가 모두 일치하는 경우 (WARN)")
    decision_2 = engine.make_decision(danger_score=0.4, safe_score=1.0, a_case_results=mock_cases)
    print(json.dumps(decision_2, indent=2, ensure_ascii=False))
    
    # 시나리오 3: 점수 차이가 모호하고, 과거 사례는 각기 다른 경우
    print("\n[3] 점수 차이가 모호한 경우 (WARN)")
    decision_3 = engine.make_decision(danger_score=1.2, safe_score=1.5, a_case_results=mock_cases_different)
    print(json.dumps(decision_3, indent=2, ensure_ascii=False))

    # 시나리오 4: 안전도가 위험도보다 월등히 높은 경우
    print("\n[4] 안전도가 월등히 높은 경우 (SAFE)")
    decision_4 = engine.make_decision(danger_score=0.3, safe_score=2.0, a_case_results=mock_cases_different)
    print(json.dumps(decision_4, indent=2, ensure_ascii=False))