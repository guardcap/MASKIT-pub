from app.utils.clova_ocr import ClovaOCR

pdf_ocr_result = ClovaOCR.parsing_pdf_json2ocr(response_json)

# 전체 텍스트
print(pdf_ocr_result.get_fulltext())

# 각 페이지 접근
for page in pdf_ocr_result.pages:
    print(f"Page {page.pageIndex}: {page.get_fulltext()}")
