import sys
import os
from PIL import Image
from app.utils.clova_ocr import clovaOCR


INPUT_PATH = "app/test/test.pdf"  # 또는 "document.pdf"

ocr = clovaOCR()

if not os.path.exists(INPUT_PATH):
    print(f"파일이 존재하지 않음: {INPUT_PATH}")
    sys.exit(1)

if INPUT_PATH.lower().endswith((".jpg", ".jpeg", ".png")):
    print("이미지 파일로 singleimage 실행 중...")
    image = Image.open(INPUT_PATH)
    result = ocr.singleimage(image)
elif INPUT_PATH.lower().endswith(".pdf"):
    print("PDF 파일로 multipdf 실행 중...")
    result = ocr.multipdf(INPUT_PATH)
else:
    print("지원하지 않는 파일 형식입니다.")
    sys.exit(1)

# 4. 결과 출력
print("\n요청 헤더:")
print(result["headers"])

print("\n페이로드 요약:")
print("RequestId:", result["payload"]["requestId"])
print("Format:", result["payload"]["images"][0]["format"])
print("Data (Base64 앞 100자):", result["payload"]["images"][0]["data"][:100])

