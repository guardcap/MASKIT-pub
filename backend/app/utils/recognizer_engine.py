from typing import List, Dict, Any, Optional
# 여러분의 AnalyzerEngine 코드가 의존하는 클래스들을 임포트합니다.
# 이 파일들이 app/utils 폴더에 있어야 합니다.
from app.utils.recognizer_registry import RecognizerRegistry
from app.utils.ner.NER_engine import NerEngine
from app.utils.entity import Entity, EntityGroup

# 여러분이 제공한 AnalyzerEngine 클래스
class AnalyzerEngine:
    """
    규칙 기반(RecognizerRegistry) + NER 기반(NerEngine) 결과를
    하나의 EntityGroup으로 통합하여 반환.
    """
    def __init__(self, db_client=None):
        print("...AnalyzerEngine 초기화 중...")
        self.db_client = db_client
        self.registry = RecognizerRegistry(db_client=db_client)
        self.registry.load_predefined_recognizers()

        self.nlp_engine = NerEngine()
        print("~AnalyzerEngine 준비 완료~")

    async def load_custom_entities(self):
        """MongoDB에서 커스텀 엔티티 로드"""
        if self.db_client is not None:
            print("📋 커스텀 엔티티 로드 중...")
            await self.registry.load_custom_recognizers()

    def analyze(self, text: str) -> EntityGroup:
        regex_group = self.registry.regex_analyze(text)
        ner_group = self.nlp_engine.ner_analyze(text)
        combined = self._merge_groups(regex_group, ner_group)
        combined.entities = self._dedup_and_sort(combined.entities)
        
        print("\n\n최종 분석 결과(EntityGroup):")
        for e in combined.entities:
            print(f" - {e.entity}: '{e.word}' ({e.start}, {e.end}) score={e.score:.2f}")

        return combined

    @staticmethod
    def _merge_groups(a: EntityGroup, b: EntityGroup) -> EntityGroup:
        merged = EntityGroup(list(a.entities))
        for e in b.entities:
            replaced = False
            for i, ea in enumerate(merged.entities):
                if ea.entity == e.entity and (ea.start < e.end and e.start < ea.end):
                    len_a = ea.end - ea.start
                    len_b = e.end - e.start
                    if len_b > len_a or (len_b == len_a and e.score > ea.score):
                        merged.entities[i] = e
                    replaced = True
                    break
            if not replaced:
                merged.entities.append(e)
        return merged

    @staticmethod
    def _dedup_and_sort(entities: List[Entity]) -> List[Entity]:
        seen = set()
        uniq: List[Entity] = []
        for e in entities:
            key = (e.entity, e.start, e.end, e.word)
            if key in seen:
                continue
            seen.add(key)
            uniq.append(e)
        uniq.sort(key=lambda x: (x.start, x.end))
        return uniq


def find_text_coordinates_in_ocr(text: str, start_pos: int, end_pos: int, ocr_pages: List[Dict]):
    """
    PII 텍스트의 전체 텍스트 내 위치를 OCR 필드의 boundingPoly 좌표로 변환합니다.
    동일한 텍스트가 여러 번 나오는 경우, start_pos와 정확히 일치하는 필드만 반환합니다.
    """
    coordinates = []
    current_pos = 0
    target_text = text[start_pos:end_pos].strip()
    
    print(f"[좌표 검색] 타겟 텍스트: '{target_text}' (위치: {start_pos}-{end_pos})")
    
    for page in ocr_pages:
        page_index = page.get("pageIndex", 0)
        fields = page.get("fields", [])
        
        print(f"[좌표 검색] 페이지 {page_index} - 필드 수: {len(fields)}")
        
        for field_idx, field in enumerate(fields):
            field_text = field.get("text", "").strip()
            if not field_text:
                current_pos += 1
                continue
                
            field_start = current_pos
            field_end = current_pos + len(field_text)
            
            # **핵심 수정: start_pos가 필드 범위 내에 정확히 포함되는 경우만 매칭**
            is_exact_match = False
            
            # 1. start_pos가 이 필드의 시작 위치와 일치하고, 텍스트도 일치
            if field_start == start_pos and target_text == field_text:
                is_exact_match = True
                print(f"[좌표 검색] 정확한 위치 매칭: 필드 시작({field_start}) == PII 시작({start_pos})")
            
            # 2. start_pos가 필드 내부에 있고, 필드가 타겟 텍스트를 포함
            elif start_pos >= field_start and start_pos < field_end and target_text in field_text:
                # 필드 내에서 타겟 텍스트의 상대 위치 확인
                relative_pos = start_pos - field_start
                if field_text[relative_pos:relative_pos + len(target_text)] == target_text:
                    is_exact_match = True
                    print(f"[좌표 검색] 필드 내부 매칭: PII({start_pos}) in Field({field_start}-{field_end})")
            
            if is_exact_match:
                bounding_poly = field.get("boundingPoly", {})
                vertices = bounding_poly.get("vertices", [])
                
                if len(vertices) >= 4:
                    x_coords = [v.get("x", 0) for v in vertices]
                    y_coords = [v.get("y", 0) for v in vertices]
                    
                    x1, x2 = min(x_coords), max(x_coords)
                    y1, y2 = min(y_coords), max(y_coords)
                    
                    margin = 2
                    bbox = [
                        max(0, x1 - margin), 
                        max(0, y1 - margin), 
                        x2 + margin, 
                        y2 + margin
                    ]
                    
                    coordinates.append({
                        "pageIndex": page_index,
                        "bbox": bbox,
                        "field_text": field_text,
                        "vertices": vertices
                    })
                    
                    print(f"[좌표 매칭 성공] PII '{target_text}' -> 페이지 {page_index}, bbox: {bbox}")
                    
                    # **중요: 정확한 매칭을 찾았으므로 즉시 반환 (중복 방지)**
                    return coordinates
            
            current_pos = field_end + 1
    
    if not coordinates:
        print(f"[좌표 매칭 실패] PII '{target_text}'에 대한 좌표를 찾을 수 없음")
    
    return coordinates


async def recognize_pii_in_text(text_content: str, ocr_data: Optional[Dict] = None, db_client=None):
    """
    텍스트 분석을 수행하고 결과를 반환하는 최종 함수
    OCR 데이터가 있으면 PII의 좌표 정보도 함께 반환
    db_client를 전달하면 MongoDB의 커스텀 엔티티도 사용
    """
    analyzer = AnalyzerEngine(db_client=db_client)

    # 커스텀 엔티티 로드 (db_client가 있는 경우)
    if db_client is not None:
        await analyzer.load_custom_entities()

    result = analyzer.analyze(text_content)

    # FastAPI가 인식할 수 있는 딕셔너리 형태로 변환
    pii_entities_list = []
    for e in result.entities:
        entity_dict = {
            "text": e.word,
            "type": e.entity,
            "score": e.score,
            "start_char": e.start,
            "end_char": e.end,
        }

        # OCR 데이터가 있으면 좌표 정보도 추가
        if ocr_data and "pages" in ocr_data:
            coordinates = find_text_coordinates_in_ocr(
                text_content, e.start, e.end, ocr_data["pages"]
            )
            entity_dict["coordinates"] = coordinates

        pii_entities_list.append(entity_dict)

    return {
        "full_text": text_content,
        "pii_entities": pii_entities_list
    }