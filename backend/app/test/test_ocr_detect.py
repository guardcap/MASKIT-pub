from app.utils.image_analyzer_engine import ImageAnalyzerEngine

# 🔎 엔진 인스턴스 생성 
analyzer_engine = ImageAnalyzerEngine()

def test_image_file_analysis(image_path: str):
    print(f"\n🔎 이미지 파일 분석 시작: {image_path}")
    
    # 수정된 analyze 메서드는 이제 bounding box 정보가 포함된 딕셔너리 리스트를 반환
    pii_fields = analyzer_engine.analyze(image_path)

    if not pii_fields:
        print("🔍 마스킹 대상 PII가 발견되지 않았습니다.")
        return

    print(f"🔍 마스킹 대상 PII 필드 수: {len(pii_fields)}")
    for idx, field in enumerate(pii_fields, 1):
        print(f"{idx}. PII: '{field['text']}'")
        print(f"   - 유형: {field['entity_type']}")
        print(f"   - 신뢰도: {field['score']:.2f}")
        print(f"   - Bounding Box: {field['boundingPoly']}")
        print("---")

if __name__ == "__main__":

    test_image_file_analysis("app/test/test.jpg")
