#!/usr/bin/env python3
"""
raw_guidelines 폴더의 모든 PDF 파일을 정책 API를 통해 업로드하는 스크립트
"""
import os
import sys
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

# 설정
API_BASE = os.getenv("API_URL", "http://localhost:8000")
UPLOAD_ENDPOINT = f"{API_BASE}/api/policies/upload"
SYNC_ENDPOINT = f"{API_BASE}/api/policies/sync/vector-store"

# PDF 파일 디렉토리
BASE_DIR = Path("/Users/6kiity/Documents/enterprise-guardcap/backend")
RAW_GUIDELINES_DIR = BASE_DIR / "app" / "rag" / "data" / "raw_guidelines"


def extract_authority_from_filename(filename: str) -> str:
    """파일명에서 발행 기관 추출"""
    filename_lower = filename.lower()

    if "금융보안원" in filename or "금융분야" in filename:
        return "금융보안원"
    elif "gdpr" in filename_lower or "eu" in filename_lower:
        return "EU"
    elif "개인정보" in filename or "pipa" in filename_lower:
        return "개인정보보호위원회"
    elif "랜섬웨어" in filename or "보안" in filename:
        return "KISA"
    else:
        return "정부기관"


def extract_title_from_filename(filename: str) -> str:
    """파일명에서 제목 추출 (확장자 제거)"""
    return Path(filename).stem


async def upload_single_policy(client: httpx.AsyncClient, file_path: Path) -> dict:
    """단일 정책 파일 업로드"""
    filename = file_path.name
    title = extract_title_from_filename(filename)
    authority = extract_authority_from_filename(filename)

    print(f"\n📄 업로드 중: {title[:50]}...")
    print(f"   발행 기관: {authority}")

    try:
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/pdf")}
            data = {
                "title": title,
                "authority": authority,
                "description": f"자동 업로드: {filename}"
            }

            response = await client.post(
                UPLOAD_ENDPOINT,
                files=files,
                data=data,
                timeout=300.0  # 5분 타임아웃 (큰 PDF 처리용)
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    policy_id = result.get("data", {}).get("policy_id", "N/A")
                    print(f"   ✅ 성공! Policy ID: {policy_id}")
                    return {"status": "success", "file": filename, "policy_id": policy_id}
                else:
                    print(f"   ❌ 실패: {result.get('message', 'Unknown error')}")
                    return {"status": "failed", "file": filename, "error": result.get("message")}
            else:
                print(f"   ❌ HTTP 오류: {response.status_code}")
                return {"status": "failed", "file": filename, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        print(f"   ❌ 예외 발생: {str(e)}")
        return {"status": "error", "file": filename, "error": str(e)}


async def sync_to_vector_store(client: httpx.AsyncClient):
    """Vector Store에 동기화"""
    print("\n\n🔄 OpenAI Vector Store 동기화 시작...")

    try:
        response = await client.post(SYNC_ENDPOINT, timeout=600.0)  # 10분 타임아웃

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                data = result.get("data", {})
                print(f"   ✅ 동기화 완료!")
                print(f"   - 추가됨: {len(data.get('synced', []))}개")
                print(f"   - 스킵됨: {len(data.get('skipped', []))}개")
                print(f"   - 실패: {len(data.get('failed', []))}개")
                return True
        else:
            print(f"   ❌ 동기화 실패: HTTP {response.status_code}")

    except Exception as e:
        print(f"   ❌ 동기화 오류: {str(e)}")

    return False


async def main():
    """메인 함수"""
    print("=" * 60)
    print("📚 정책 PDF 일괄 업로드 스크립트")
    print("=" * 60)
    print(f"API 서버: {API_BASE}")
    print(f"PDF 디렉토리: {RAW_GUIDELINES_DIR}")

    # PDF 파일 목록 확인
    if not RAW_GUIDELINES_DIR.exists():
        print(f"\n❌ 디렉토리가 존재하지 않습니다: {RAW_GUIDELINES_DIR}")
        sys.exit(1)

    pdf_files = list(RAW_GUIDELINES_DIR.glob("*.pdf"))
    print(f"\n📁 발견된 PDF 파일: {len(pdf_files)}개")

    if not pdf_files:
        print("❌ 업로드할 PDF 파일이 없습니다.")
        sys.exit(1)

    # 파일 목록 출력
    print("\n" + "-" * 40)
    for i, f in enumerate(pdf_files, 1):
        print(f"  {i:2d}. {f.name[:60]}...")
    print("-" * 40)

    # 자동 실행 모드 (--auto 인자)
    auto_mode = "--auto" in sys.argv
    if not auto_mode:
        confirm = input(f"\n{len(pdf_files)}개 파일을 업로드하시겠습니까? (y/N): ")
        if confirm.lower() != 'y':
            print("취소되었습니다.")
            sys.exit(0)
    else:
        print(f"\n🚀 자동 모드: {len(pdf_files)}개 파일 업로드 시작...")

    # 업로드 시작
    start_time = datetime.now()
    results = {"success": [], "failed": [], "error": []}

    async with httpx.AsyncClient() as client:
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}]", end="")
            result = await upload_single_policy(client, pdf_file)
            results[result["status"]].append(result)

            # 너무 빠른 요청 방지
            await asyncio.sleep(1)

        # Vector Store 동기화
        print("\n" + "=" * 60)
        await sync_to_vector_store(client)

    # 결과 출력
    elapsed = datetime.now() - start_time
    print("\n" + "=" * 60)
    print("📊 업로드 결과 요약")
    print("=" * 60)
    print(f"   ✅ 성공: {len(results['success'])}개")
    print(f"   ❌ 실패: {len(results['failed'])}개")
    print(f"   ⚠️  오류: {len(results['error'])}개")
    print(f"   ⏱️  소요 시간: {elapsed}")

    if results['failed']:
        print("\n실패한 파일:")
        for r in results['failed']:
            print(f"   - {r['file']}: {r.get('error', 'Unknown')}")

    if results['error']:
        print("\n오류 발생 파일:")
        for r in results['error']:
            print(f"   - {r['file']}: {r.get('error', 'Unknown')}")

    print("\n✅ 완료!")


if __name__ == "__main__":
    asyncio.run(main())
