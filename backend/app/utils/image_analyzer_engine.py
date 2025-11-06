from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.recognizer_registry import RecognizerRegistry
from presidio_analyzer.pattern_recognizer import PatternRecognizer, Pattern
from .clova_ocr import ClovaOCR, OCRResult
from typing import List, Dict, Any

class ImageAnalyzerEngine:
    def __init__(
            self,
            analyzer_engine: AnalyzerEngine = None,
            ocr: ClovaOCR = None,
    ):
        if not analyzer_engine:
            # NLP 엔진 설정 (en_core_web_lg 모델이 설치되어 있어야 함)
            configuration = {
                "nlp_engine_name": "spacy",
                "models": [
                    {"lang_code": "en", "model_name": "en_core_web_lg"}
                ],
            }
            nlp_engine_provider = NlpEngineProvider(nlp_configuration=configuration)
            nlp_engine = nlp_engine_provider.create_engine()

            # Presidio에 내장된 영문 인식기만 로드
            registry = RecognizerRegistry()
            registry.load_predefined_recognizers(languages=["en"])
            
            analyzer_engine = AnalyzerEngine(
                registry=registry,
                nlp_engine=nlp_engine,
                supported_languages=["en"] # 영어를 지원 언어에 추가
            )
        self.analyzer_engine = analyzer_engine

        if not ocr:
            ocr = ClovaOCR()
        self.ocr = ocr

    def analyze(self, file_path: str) -> List[Dict[str, Any]]:
        # OCR 결과 추출
        if not file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            print("지원되지 않는 파일 형식입니다.")
            return []

        # ClovaOCR의 singleimage는 이제 OCRResult 객체를 반환
        ocr_result: OCRResult = self.ocr.singleimage(file_path)

        if not ocr_result.success:
            print("OCR을 로드할 수 없거나 API 호출에 실패했습니다.")
            return []

        # OCR 결과에서 full_text 추출
        text = ocr_result.get_fulltext()
        if not text:
            print("OCR 결과에 텍스트가 없습니다.")
            return []
        
        # 테스트 이미지에 맞춰 'en'으로 지정합니다.
        detected_language = 'en'
        print(f"추출된 텍스트 언어: {detected_language}")

        # Presidio Analyzer를 사용하여 텍스트 분석
        analyzer_results = self.analyzer_engine.analyze(text, language=detected_language)
        
        # PII 결과와 OCR bounding box 매핑
        masking_fields = []
        
        # OCR 결과를 기반으로 text와 start/end 위치를 정확하게 재구성
        reconstructed_text_with_pos = []
        current_pos = 0
        for field in ocr_result.fields:
            field_text = field.get('text', '')
            if field_text:
                reconstructed_text_with_pos.append({
                    'text': field_text,
                    'start': current_pos,
                    'end': current_pos + len(field_text),
                    'boundingPoly': field.get('boundingPoly', {})
                })
                current_pos += len(field_text) + 1  # 띄어쓰기

        for result in analyzer_results:
            # Presidio 결과의 위치에 해당하는 원본 OCR 필드 찾기
            pii_text = text[result.start:result.end]
            for field in reconstructed_text_with_pos:
                # 대소문자 무시하고 일치 여부 확인
                if field['text'].lower() == pii_text.lower():
                    masking_fields.append({
                        "text": field['text'],  # 원본 텍스트 사용
                        "entity_type": result.entity_type,
                        "score": result.score,
                        "boundingPoly": field['boundingPoly']
                    })
                    break # 매핑 완료 후 다음 Presidio 결과로 이동

        return masking_fields
