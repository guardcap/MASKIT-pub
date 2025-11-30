# scripts/llm_client.py
import ollama
from typing import Dict, Any, Tuple, List
import json

class Entity:
    def __init__(
        self,
        entity: str,
        score: float,
        word: str,
        start: int,
        end: int,
        pageIndex: int = None,
        bbox: Tuple[int, int, int, int] = None
    ):
        self.entity = entity              # 엔티티 종류 (예: "EMAIL", "NAME")
        self.score = score                # 신뢰도 점수
        self.word = word                  # 인식된 단어 또는 텍스트
        self.start = start                # 텍스트 내 시작 인덱스
        self.end = end                    # 텍스트 내 끝 인덱스
        self.pageIndex = pageIndex        # 해당 OCR 페이지 번호
        self.bbox = bbox                  # Bounding Box (x1, y1, x2, y2)

class LLMClient:
    def __init__(self, model: str = "llama3"):
        self.model = model
   
    # checklist는 사이드바에서 선택한, entities는 엔티티 추출 결과, doc_summary는 메일 본문+OCR 추출 텍스트 
    def chat(self, system: str, checklist: Dict[str, Any], entities: List[Entity], doc_summary: str, max_tokens: int = 2048, temperature: float = 0.0) -> str:
        """
        Ollama chat wrapper. returns the model content string.
        system=SYSTEM_PROMPT, checklist, entities, doc_summary
        """
        checklist_str = json.dumps(checklist, indent=2, ensure_ascii=False)
        
        # [수정된 부분] Entity 객체 리스트를 딕셔너리 리스트로 변환합니다.
        # vars(e)는 각 Entity 객체 e의 속성을 담은 딕셔너리를 반환합니다.
        entities_list_of_dicts = [vars(e) for e in entities]
        entities_str = json.dumps(entities_list_of_dicts, indent=2, ensure_ascii=False)
        
        user_prompt =f"""
        ### 다음은 사용자 지정 config(checklist), 이메일 본문 및 첨부파일 OCR 결과 모음(doc_summary), 추출된 엔티티(entities)입니다.
        ```json
        {checklist_str}
        ```
        
        ```json
        {entities_str}
        ```
        
        ```text
        {doc_summary}
        ```
        """
        resp = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt}
            ],
            options={
                "temperature": temperature,
                "num_predict": max_tokens
            }
        )
        
        return resp["message"]["content"]
