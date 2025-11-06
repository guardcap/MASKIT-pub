import sys
from pathlib import Path
from markitdown import MarkItDown

def convert_file_to_md(input_path: str):
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {input_path}")
        return

    # 출력 파일 이름: 같은 이름 + .md 확장자
    output_file = input_file.with_suffix(".md")

    # markitdown 변환
    md = MarkItDown()
    try:
        result = md.convert(str(input_file))
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.text_content)
        print(f"✅ 변환 완료: {input_file.name} → {output_file.name}")
    except Exception as e:
        print(f"⚠️ 변환 실패: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python convert_file_to_md.py <파일경로>")
    else:
        convert_file_to_md(sys.argv[1])
