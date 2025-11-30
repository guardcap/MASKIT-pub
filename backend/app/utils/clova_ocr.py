import uuid
import base64
import os
import requests
import json
from PIL import Image
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

class OCRResult:
    def __init__(self):
        self.success: bool = False
        self.image_name: str = ""
        self.pageIndex: int = 0
        self.fields: List[Dict[str, Any]] = []
        self.full_text: str = ""

    def __repr__(self):
        return (
            f"OCRResult(success={self.success}, "
            f"image_name='{self.image_name}', "
            f"fields_count={len(self.fields)}, "
            f"full_text='{self.full_text[:30]}...')"
        )

    def get_fulltext(self):
        return self.full_text

class PdfOCRResult:
    def __init__(self):
        self.pages: List[OCRResult] = []
        self.full_text: str = ""

    def get_fulltext(self):
        return self.full_text

class ClovaOCR:
    def __init__(self, url: str = None, key: str = None):
        self.url = url or os.getenv("CLOVA_OCR_URL")
        self.secret_key = key or os.getenv("CLOVA_OCR_SECRET")

    def singleimage(self, image: object, **kwargs) -> OCRResult:
        """
        이미지 파일을 Clova OCR API로 전송하고 결과를 파싱하여 OCRResult 객체를 반환합니다.
        """
        if isinstance(image, str):
            if not os.path.exists(image):
                raise FileNotFoundError(f"이미지 파일이 존재하지 않음: {image}")
            with open(image, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            image_format = os.path.splitext(image)[1][1:].upper()
        elif isinstance(image, Image.Image):
            from io import BytesIO
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            image_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
            image_format = "PNG"
        else:
            raise TypeError("image는 str 경로 또는 PIL.Image.Image 객체여야 합니다.")

        headers = {
            "X-OCR-SECRET": self.secret_key,
            "Content-Type": "application/json"
        }

        payload = {
            "version": "V2",
            "requestId": str(uuid.uuid4()),
            "timestamp": kwargs.get("timestamp", 0),
            "images": [
                {
                    "name": kwargs.get("name", "sample_image"),
                    "format": image_format,
                    "data": image_data,
                    "url": None
                }
            ]
        }

        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            response_json = response.json()
            return self.parsing_json2ocr(response_json)
        except requests.exceptions.RequestException as e:
            print(f"[ClovaOCR] API 호출 오류: {e}")
            return OCRResult()
        except json.JSONDecodeError:
            print("[ClovaOCR] JSON 파싱 오류: API 응답이 유효한 JSON 형식이 아닙니다.")
            return OCRResult()

    def multipdf(self, file: object, **kwargs) -> PdfOCRResult:
        # PDF 처리는 현재 로직에서 사용되지 않으므로 원본 코드 유지
        if isinstance(file, str):
            if not os.path.exists(file):
                raise FileNotFoundError(f"PDF 파일이 존재하지 않음: {file}")
            with open(file, "rb") as f:
                pdf_data = base64.b64encode(f.read()).decode("utf-8")
        elif hasattr(file, "read"):
            pdf_data = base64.b64encode(file.read()).decode("utf-8")
        else:
            raise TypeError("file은 str 경로나 바이너리 stream이어야 합니다.")

        headers = {
            "X-OCR-SECRET": self.secret_key,
            "Content-Type": "application/json"
        }

        payload = {
            "version": "V2",
            "requestId": str(uuid.uuid4()),
            "timestamp": kwargs.get("timestamp", 0),
            "images": [
                {
                    "name": kwargs.get("name", "sample_pdf"),
                    "format": "pdf",
                    "data": pdf_data,
                    "url": None
                }
            ]
        }
        
        # API 호출 및 파싱 로직 추가 필요
        # ...

        return PdfOCRResult()

    @staticmethod
    def parsing_json2ocr(response_json: Dict[str, Any]) -> OCRResult:
        result = OCRResult()
        try:
            image_data = response_json["images"][0]
            result.success = image_data.get("inferResult") == "SUCCESS"
            result.image_name = image_data.get("name", "")
            result.pageIndex = image_data.get("pageIndex")
            
            full_text = []
            for field in image_data.get("fields", []):
                field_entry = {
                    "text": field.get("inferText"),
                    "confidence": field.get("inferConfidence"),
                    "lineBreak": field.get("lineBreak"),
                    "boundingPoly": field.get("boundingPoly", {}),
                }
                result.fields.append(field_entry)
                full_text.append(field.get("inferText", ""))

            result.full_text = " ".join(full_text)
        except (KeyError, IndexError, TypeError) as e:
            print(f"[ClovaOCR] Error during parsing: {e}")
        return result
    
    @staticmethod
    def parsing_pdf_json2ocr(response_json: Dict[str, Any]) -> PdfOCRResult:
        # PDF 처리는 현재 로직에서 사용되지 않으므로 원본 코드 유지
        pdf_result = PdfOCRResult()
        all_text = []
        for image_data in response_json.get("images", []):
            ocr_result = OCRResult()
            ocr_result.success = image_data.get("inferResult") == "SUCCESS"
            ocr_result.image_name = image_data.get("name", "")
            ocr_result.pageIndex = image_data.get("pageIndex", 0)
            full_text = []
            for field in image_data.get("fields", []):
                entry = {
                    "text": field.get("inferText"),
                    "confidence": field.get("inferConfidence"),
                    "lineBreak": field.get("lineBreak"),
                    "boundingPoly": field.get("boundingPoly", {})
                }
                ocr_result.fields.append(entry)
                full_text.append(field.get("inferText", ""))
            ocr_result.full_text = " ".join(full_text)
            all_text.append(ocr_result.full_text)
            pdf_result.pages.append(ocr_result)
        pdf_result.full_text = "\n".join(all_text)
        return pdf_result
