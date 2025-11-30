import uuid
import base64
import os
import requests
import json
from PIL import Image
from dotenv import load_dotenv
from typing import List, Dict, Any
from io import BytesIO

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
        if isinstance(image, str):
            if not os.path.exists(image):
                raise FileNotFoundError(f"이미지 파일이 존재하지 않음: {image}")
            with open(image, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            image_format = os.path.splitext(image)[1][1:].upper()
        elif isinstance(image, Image.Image):
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
        
        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            response_json = response.json()
            return self.parsing_pdf_json2ocr(response_json)
        except requests.exceptions.RequestException as e:
            print(f"[ClovaOCR] API 호출 오류: {e}")
            return PdfOCRResult()
        except json.JSONDecodeError:
            print("[ClovaOCR] JSON 파싱 오류: API 응답이 유효한 JSON 형식이 아닙니다.")
            return PdfOCRResult()

    @staticmethod
    def parsing_json2ocr(response_json: Dict[str, Any]) -> OCRResult:
        result = OCRResult()
        try:
            image_data = response_json["images"][0]
            result.success = image_data.get("inferResult") == "SUCCESS"
            result.image_name = image_data.get("name", "")
            result.pageIndex = image_data.get("pageIndex", 0)
            
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


def extract_text_from_file(file_content: bytes, file_name: str):
    """
    파일의 확장자를 기반으로 OCR을 수행하고 결과를 반환합니다.
    OCR 좌표 정보도 함께 반환하여 PII 마스킹 시 사용할 수 있도록 합니다.
    """
    
    clova_ocr_instance = ClovaOCR()
    
    if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        # 이미지 파일 처리
        ocr_result = clova_ocr_instance.singleimage(Image.open(BytesIO(file_content)))
        return {
            "full_text": ocr_result.full_text,
            "pages": [{
                "pageIndex": ocr_result.pageIndex,
                "fields": ocr_result.fields
            }]
        }
    elif file_name.lower().endswith('.pdf'):
        # PDF 파일 처리
        pdf_result = clova_ocr_instance.multipdf(BytesIO(file_content))
        pages_data = []
        for page in pdf_result.pages:
            pages_data.append({
                "pageIndex": page.pageIndex,
                "fields": page.fields
            })
        return {
            "full_text": pdf_result.full_text,
            "pages": pages_data
        }
    else:
        return {
            "full_text": "지원하지 않는 파일 형식입니다.",
            "pages": []
        }