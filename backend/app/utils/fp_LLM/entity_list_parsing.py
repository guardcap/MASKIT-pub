"""현재 포함된 entity list 만들기
recognizer_dir = "app/utils/recognizer"
result = collect_entity_keywords(recognizer_dir)
이런 식으로 함수 호출하여 사용 """
import os
import re
import importlib.util
from typing import Dict, List

def collect_entity_keywords(directory: str) -> Dict[str, List[str]]:
    entity_keywords_map = {}

    for filename in os.listdir(directory):
        if not filename.endswith(".py") or filename.startswith("__"):
            continue

        filepath = os.path.join(directory, filename)

        # 파일 내용 읽기
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # KEYWORDS 추출
        keywords_match = re.search(r'KEYWORDS\s*=\s*(\[[^\]]*\])', content)
        keywords_list = []
        if keywords_match:
            try:
                keywords_list = eval(keywords_match.group(1))
            except Exception:
                pass

        # 엔티티명 추출 (return {"ENTITY": ...} 형태)
        entity_match = re.search(r'return\s*{\s*[\'"]([A-Z_]+)[\'"]\s*:', content)
        if entity_match:
            entity_name = entity_match.group(1)
            entity_keywords_map[entity_name] = keywords_list

    return entity_keywords_map
