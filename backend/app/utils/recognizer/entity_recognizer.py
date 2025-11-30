from typing import List, Dict, Union

class EntityRecognizer:
    """
    모든 엔티티 인식기의 기본 클래스  
    하위 클래스에서 `analyze` 메서드를 구현해야   
    """
    def __init__(self, name: str, supported_entities: List[str]):
        self.name = name
        self.supported_entities = supported_entities

    def analyze(self, text: str) -> Dict[str, Union[List[str], List[Dict]]]:
        """
        주어진 텍스트에서 엔티티를 분석하고 결과를 반환  
        
        :param text: 분석할 텍스트.
        :return: 각 엔티티 타 별로 발견된 값들의 딕셔너리.
        """