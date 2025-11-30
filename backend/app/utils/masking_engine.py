import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import os
from typing import List, Dict, Any

class UnifiedMaskingEngine:
    """
    PDF와 이미지 파일(PNG, JPG 등)을 모두 처리할 수 있는 통합 마스킹 엔진
    """
    
    def __init__(self):
        self.mask_color = (0, 0, 0)  # 검은색 마스킹
        
    def redact_pdf_with_entities(self, pdf_path: str, entities: List[Dict], out_pdf_path: str):
        """
        파일 확장자에 따라 PDF 또는 이미지 마스킹을 수행합니다.
        """
        file_ext = os.path.splitext(pdf_path)[1].lower()
        
        if file_ext == '.pdf':
            self._mask_pdf_file(pdf_path, entities, out_pdf_path)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            self._mask_image_file(pdf_path, entities, out_pdf_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {file_ext}")
    
    def _mask_pdf_file(self, pdf_path: str, entities: List[Dict], out_pdf_path: str):
        """
        PDF 파일을 마스킹합니다.
        """
        try:
            print(f"[PDF 마스킹] 파일 열기: {pdf_path}")
            doc = fitz.open(pdf_path)

            for entity in entities:
                pii_text = entity.get("text", "")
                entity_type = entity.get("entity", "")
                target_page = entity.get("pageIndex", 0)
                bbox = entity.get("bbox", None)
                instance_index = entity.get("instance_index", None)

                print(f"[PDF 마스킹] 검색 중: '{pii_text}' (타입: {entity_type}, 페이지: {target_page}, bbox: {bbox}, 인스턴스: {instance_index})")

                if not pii_text.strip():
                    print(f"[PDF 마스킹] 빈 텍스트 스킵: {entity}")
                    continue

                if target_page < len(doc):
                    page = doc[target_page]
                    # bbox가 있으면 bbox로 직접 마스킹
                    if bbox and len(bbox) == 4:
                        self._mask_by_bbox(page, bbox, pii_text)
                    else:
                        # bbox가 없으면 텍스트 검색 + instance_index 사용
                        self._mask_text_in_pdf_page(page, pii_text, entity_type, instance_index=instance_index)
                else:
                    print(f"[PDF 마스킹] 잘못된 페이지 번호 {target_page}")

            print(f"[PDF 마스킹] 저장 중: {out_pdf_path}")
            doc.save(out_pdf_path)
            doc.close()
            print(f"[✔] PDF 저장 완료: {out_pdf_path}")

        except Exception as e:
            print(f"[PDF 마스킹 오류] {e}")
            import traceback
            traceback.print_exc()
            raise e

    def _mask_by_bbox(self, page, bbox: List[float], pii_text: str):
        """
        bbox 좌표를 사용하여 직접 마스킹합니다.
        """
        x1, y1, x2, y2 = bbox
        rect = fitz.Rect(x1, y1, x2, y2)
        print(f"[PDF 마스킹] bbox로 마스킹: '{pii_text}' at {rect}")
        page.draw_rect(rect, color=self.mask_color, fill=self.mask_color)
    
    def _mask_image_file(self, image_path: str, entities: List[Dict], out_image_path: str):
        """
        이미지 파일을 마스킹합니다. OCR bbox 좌표를 사용합니다.
        """
        try:
            print(f"[이미지 마스킹] 파일 열기: {image_path}")
            
            # PIL로 이미지 열기
            with Image.open(image_path) as img:
                # RGB 모드로 변환
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                draw = ImageDraw.Draw(img)
                
                # 각 엔티티에 대해 마스킹 수행
                for entity in entities:
                    pii_text = entity.get("text", "")
                    entity_type = entity.get("entity", "")
                    bbox = entity.get("bbox", [])
                    
                    print(f"[이미지 마스킹] 처리 중: '{pii_text}' (타입: {entity_type})")
                    print(f"  bbox: {bbox}")
                    
                    if not bbox or len(bbox) != 4:
                        print(f"[이미지 마스킹] 유효하지 않은 bbox: {bbox}")
                        continue
                    
                    # bbox 좌표로 검은색 사각형 그리기
                    x1, y1, x2, y2 = bbox
                    
                    # 좌표 유효성 검사
                    img_width, img_height = img.size
                    x1 = max(0, min(x1, img_width))
                    y1 = max(0, min(y1, img_height))
                    x2 = max(x1, min(x2, img_width))
                    y2 = max(y1, min(y2, img_height))
                    
                    print(f"  조정된 좌표: ({x1}, {y1}, {x2}, {y2})")
                    
                    # 검은색 사각형으로 마스킹
                    draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0))
                
                # 마스킹된 이미지 저장
                print(f"[이미지 마스킹] 저장 중: {out_image_path}")
                
                # 출력 파일 확장자에 맞춰 저장
                out_ext = os.path.splitext(out_image_path)[1].lower()
                if out_ext == '.jpg' or out_ext == '.jpeg':
                    img.save(out_image_path, 'JPEG', quality=95)
                else:
                    img.save(out_image_path, 'PNG')
                
                print(f"[✔] 이미지 저장 완료: {out_image_path}")
                
        except Exception as e:
            print(f"[이미지 마스킹 오류] {e}")
            import traceback
            traceback.print_exc()
            raise e
    
    def _mask_text_in_pdf_page(self, page, search_text: str, entity_type: str, instance_index: int = None):
        """
        PDF 페이지에서 특정 텍스트를 찾아 마스킹합니다.
        instance_index가 제공되면 해당 순서의 인스턴스만 마스킹합니다.
        """
        text_instances = page.search_for(search_text)
        
        if text_instances:
            print(f"[PDF 마스킹] 페이지 {page.number}에서 '{search_text}' 발견: {len(text_instances)}개")
            
            # instance_index가 지정된 경우 해당 인덱스만 마스킹
            if instance_index is not None:
                if 0 <= instance_index < len(text_instances):
                    rect = text_instances[instance_index]
                    print(f"[PDF 마스킹] 인스턴스 {instance_index} 마스킹: {rect}")
                    page.draw_rect(rect, color=self.mask_color, fill=self.mask_color)
                else:
                    print(f"[PDF 마스킹] 잘못된 인스턴스 인덱스: {instance_index}")
            else:
                # 인덱스가 없으면 모든 인스턴스 마스킹 (기존 동작)
                for i, rect in enumerate(text_instances):
                    print(f"  위치 {i+1}: {rect}")
                    page.draw_rect(rect, color=self.mask_color, fill=self.mask_color)
        else:
            self._fuzzy_search_and_mask_pdf(page, search_text, entity_type)
    
    def _fuzzy_search_and_mask_pdf(self, page, search_text: str, entity_type: str):
        """
        PDF에서 정확한 매칭이 실패했을 때 퍼지 검색을 수행합니다.
        """
        print(f"[PDF 마스킹] 퍼지 검색 시작: '{search_text}'")
        
        # 페이지의 모든 텍스트 블록 가져오기
        text_dict = page.get_text("dict")
        
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        span_text = span["text"]
                        
                        # 다양한 방식으로 텍스트 매칭 시도
                        if self._is_text_match(search_text, span_text):
                            # span의 bbox 좌표 사용
                            bbox = span["bbox"]
                            rect = fitz.Rect(bbox)
                            
                            print(f"[PDF 마스킹] 퍼지 매칭 성공: '{search_text}' in '{span_text}'")
                            print(f"  좌표: {rect}")
                            
                            # 마스킹 적용
                            page.draw_rect(rect, color=self.mask_color, fill=self.mask_color)
                            return True
        
        # 그래도 찾지 못한 경우 단어별 검색
        return self._word_by_word_search_pdf(page, search_text, entity_type)
    
    def _is_text_match(self, search_text: str, span_text: str) -> bool:
        """
        두 텍스트가 매칭되는지 다양한 방식으로 확인합니다.
        """
        # 정확한 매칭
        if search_text == span_text:
            return True
        
        # 대소문자 무시 매칭
        if search_text.lower() == span_text.lower():
            return True
        
        # 공백 제거 후 매칭
        if search_text.replace(" ", "") == span_text.replace(" ", ""):
            return True
        
        # 부분 문자열 매칭
        if search_text in span_text or span_text in search_text:
            return True
        
        # 한글의 경우 조사 등이 붙을 수 있으므로 부분 매칭
        if len(search_text) >= 3:
            if search_text in span_text:
                return True
        
        return False
    
    def _word_by_word_search_pdf(self, page, search_text: str, entity_type: str) -> bool:
        """
        PDF에서 단어별로 쪼개서 검색하는 마지막 시도입니다.
        """
        print(f"[PDF 마스킹] 단어별 검색: '{search_text}'")
        
        # 공백으로 단어 분리
        words = search_text.split()
        
        for word in words:
            if len(word.strip()) >= 2:  # 최소 2글자 이상만 검색
                text_instances = page.search_for(word.strip())
                if text_instances:
                    print(f"[PDF 마스킹] 단어 '{word}' 발견: {len(text_instances)}개")
                    for rect in text_instances:
                        page.draw_rect(rect, color=self.mask_color, fill=self.mask_color)
                    return True
        
        print(f"[PDF 마스킹] 텍스트 '{search_text}'를 찾을 수 없음")
        return False
    
    def debug_pdf_text(self, pdf_path: str, page_num: int = 0):
        """
        디버깅을 위해 PDF 페이지의 모든 텍스트를 출력합니다.
        """
        doc = fitz.open(pdf_path)
        if page_num < len(doc):
            page = doc[page_num]
            text_dict = page.get_text("dict")
            
            print(f"\n[디버깅] PDF 페이지 {page_num}의 모든 텍스트:")
            for block_num, block in enumerate(text_dict["blocks"]):
                if "lines" in block:
                    print(f"\n블록 {block_num}:")
                    for line_num, line in enumerate(block["lines"]):
                        for span_num, span in enumerate(line["spans"]):
                            span_text = span["text"]
                            bbox = span["bbox"]
                            print(f"  Line {line_num}, Span {span_num}: '{span_text}' @ {bbox}")
        
        doc.close()
    
    def debug_image_info(self, image_path: str):
        """
        디버깅을 위해 이미지 정보를 출력합니다.
        """
        with Image.open(image_path) as img:
            print(f"\n[디버깅] 이미지 정보:")
            print(f"  파일: {image_path}")
            print(f"  크기: {img.size}")
            print(f"  모드: {img.mode}")


# 기존 클래스명과의 호환성을 위한 별칭
class PdfMaskingEngine(UnifiedMaskingEngine):
    """기존 코드와의 호환성을 위한 별칭"""
    pass


# 기존 API와 호환성을 위한 래퍼 함수들
def create_masking_engine():
    """기존 코드와의 호환성을 위한 팩토리 함수"""
    return PdfMaskingEngine()


# 테스트용 함수
def test_masking_engine(file_path: str, test_text: str, test_bbox: List[int] = None):
    """
    마스킹 엔진을 테스트하기 위한 함수
    """
    engine = UnifiedMaskingEngine()
    
    # 파일 타입에 따른 디버깅 정보 출력
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        print("=== PDF 텍스트 디버깅 ===")
        engine.debug_pdf_text(file_path, 0)
    elif file_ext in ['.png', '.jpg', '.jpeg']:
        print("=== 이미지 정보 디버깅 ===")
        engine.debug_image_info(file_path)
    
    # 테스트 마스킹
    if file_ext == '.pdf':
        test_entities = [{
            "text": test_text,
            "entity": "TEST",
            "pageIndex": 0
        }]
    else:
        if not test_bbox:
            print("이미지 파일 테스트를 위해서는 bbox 좌표가 필요합니다.")
            return
        test_entities = [{
            "text": test_text,
            "entity": "TEST",
            "pageIndex": 0,
            "bbox": test_bbox
        }]
    
    output_path = file_path.replace(file_ext, f'_test_masked{file_ext}')
    engine.redact_pdf_with_entities(file_path, test_entities, output_path)
    
    print(f"테스트 완료: {output_path}")