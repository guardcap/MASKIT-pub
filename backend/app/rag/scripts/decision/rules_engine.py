import os
import sys

# 상위 폴더의 모듈을 가져올 수 있도록 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.signal_extractor import SignalExtractor

class RulesEngine:
    """
    검색된 근거(evidence)와 TaskProfile을 기반으로 최종 액션을 결정하는 엔진.
    1. 신호 추출 -> 2. 점수화 -> 3. 가중치 결합 -> 4. 최종 결정
    """

    def __init__(self):
        self.signal_extractor = SignalExtractor()
        
        # 각 신호를 기본 점수로 변환하는 맵
        self.score_map = {
            "DANGER": 1.0,
            "WARN": 0.6,
            "SAFE": 0.2,
            "NONE": 0.0
        }

    def _determine_weights(self, legal_priority: str) -> dict:
        """TaskProfile의 legal_priority에 따라 가중치를 결정한다."""
        if legal_priority == "LAW_OVER_POLICY":
            # 법령(C)에 가장 높은 가중치 부여
            return {"A": 0.2, "B": 0.3, "C": 0.5}
        elif legal_priority == "POLICY_OVER_LAW":
            # 사내 규정(B)에 가장 높은 가중치 부여
            return {"A": 0.2, "B": 0.5, "C": 0.3}
        else: # 기본값 (균등)
            return {"A": 1/3, "B": 1/3, "C": 1/3}

    def decide_action(self, evidence_list: list, task_profile: dict):
        """
        근거 목록과 태스크 프로필을 바탕으로 최종 결정을 내린다.

        Args:
            evidence_list (list): Retriever가 반환한 근거 문서 목록. 
                                  각 요소는 {'source': 'A', 'text': '...'} 형태를 가정.
            task_profile (dict): 사용자의 태스크 정보. {'legal_priority': '...'} 포함.
        
        Returns:
            dict: 최종 결정 정보.
        """
        legal_priority = task_profile.get("legal_priority", "DEFAULT")
        weights = self._determine_weights(legal_priority)

        # 신호별 가중 점수 합산
        total_scores = {
            "DANGER": 0.0,
            "WARN": 0.0,
            "SAFE": 0.0,
        }

        for evidence in evidence_list:
            source = evidence.get("source") # 'A', 'B', 'C'
            text = evidence.get("text")
            
            if not source or not text:
                continue

            signal = self.signal_extractor.extract_signal(text)
            
            if signal != "NONE":
                base_score = self.score_map[signal]
                weight = weights.get(source, 0.33) # 해당 소스의 가중치
                total_scores[signal] += base_score * weight

        # --- 최종 결정 트리 ---
        DANGER_THRESHOLD = 0.4 # 위험 신호가 이 임계값을 넘으면 즉시 'BLOCK' (조정 필요)

        if total_scores["DANGER"] > DANGER_THRESHOLD:
            final_action = "BLOCK"
            reason = f"위험(DANGER) 점수({total_scores['DANGER']:.2f})가 임계점({DANGER_THRESHOLD})을 초과했습니다."
        else:
            # DANGER 점수가 임계값 미만일 때, WARN과 SAFE 점수를 비교
            if total_scores["WARN"] >= total_scores["SAFE"]:
                final_action = "MASK_PARTIAL" # WARN이 SAFE보다 높거나 같으면 부분 마스킹
                reason = f"주의(WARN) 점수({total_scores['WARN']:.2f})가 안전(SAFE) 점수({total_scores['SAFE']:.2f})보다 높아 부분 마스킹을 권장합니다."
            else:
                final_action = "KEEP" # SAFE가 가장 높으면 유지
                reason = f"안전(SAFE) 점수({total_scores['SAFE']:.2f})가 가장 높아 원본 유지를 권장합니다."

        return {
            "final_action": final_action,
            "reason": reason,
            "detailed_scores": total_scores
        }


# --- 사용 예시 ---
if __name__ == '__main__':
    engine = RulesEngine()

    # 가상의 TaskProfile
    mock_task_profile = {
        "category": "외부",
        "purpose": "WINNER_NOTICE",
        "legal_priority": "LAW_OVER_POLICY" # 법률 우선!
    }

    # 가상의 검색된 근거 목록 (HybridRetriever가 반환했다고 가정)
    mock_evidence = [
        {"source": "C", "text": "법: 개인정보 제3자 제공은 원칙적으로 금지된다."}, # DANGER, 가중치 0.5
        {"source": "B", "text": "규정: 당첨자 공지 시 이름 일부는 마스킹 처리한다."}, # WARN, 가중치 0.3
        {"source": "A", "text": "과거 사례: 이전 당첨자 공지에서 이름 가운데 글자를 별표(*) 처리함."} # WARN, 가중치 0.2
    ]

    decision = engine.decide_action(mock_evidence, mock_task_profile)

    print("--- 최종 결정 ---")
    print(f"결정: {decision['final_action']}")
    print(f"사유: {decision['reason']}")
    print("\n--- 상세 점수 ---")
    for signal, score in decision['detailed_scores'].items():
        print(f"  - {signal}: {score:.4f}")
        
    # 예상 결과:
    # DANGER 점수 = 1.0 * 0.5 = 0.5
    # WARN 점수 = 0.6 * 0.3 + 0.6 * 0.2 = 0.18 + 0.12 = 0.3
    # SAFE 점수 = 0
    # DANGER 점수가 임계값(0.4)을 넘었으므로 최종 결정은 'BLOCK'