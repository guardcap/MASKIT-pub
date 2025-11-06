"""
최적화 버전 - 병렬 배치 처리
원본 파일 백업용으로 별도 저장
"""

# 기존 process_guidelines.py의 _process_large_pdf 메서드를
# 다음과 같이 수정하면 병렬 처리 가능:

async def _process_large_pdf_parallel(
    self,
    pdf_path: str,
    pdf_path_obj: Path,
    authority: str,
    max_concurrent: int = 3  # 동시 처리 배치 수
) -> List[ApplicationGuide]:
    """대용량 PDF 병렬 배치 처리"""
    print("🔪 Splitting PDF into smaller batches...")

    batch_dir = self.temp_dir / f"batches_{pdf_path_obj.stem}"
    batch_files = self.pdf_processor.split_pdf_by_pages(pdf_path, batch_dir)

    print(f"✅ Created {len(batch_files)} batches")

    all_guides = []

    # 세마포어로 동시 실행 제한
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_single_batch(i: int, batch_file: Path):
        async with semaphore:
            try:
                result = await zerox(
                    file_path=str(batch_file),
                    model=self.vision_model,
                    output_dir=str(self.temp_dir / f"batch_{i}"),
                    cleanup=True,
                )

                markdown = result.get("content", "") if isinstance(result, dict) else str(result)

                guides = await self._structure_document(
                    markdown,
                    source_document=f"{pdf_path_obj.name} (batch {i+1}/{len(batch_files)})",
                    authority=authority
                )

                return guides

            except Exception as e:
                print(f"⚠️  Batch {i+1} failed: {e}")
                return []

    # 모든 배치를 동시에 처리
    tasks = [process_single_batch(i, batch_file) for i, batch_file in enumerate(batch_files)]
    results = await asyncio.gather(*tasks)

    # 결과 병합
    for guides in results:
        all_guides.extend(guides)

    # 임시 파일 정리
    import shutil
    shutil.rmtree(batch_dir, ignore_errors=True)

    return all_guides


# 사용법: process_guidelines.py 파일의 _process_large_pdf 메서드를 위 코드로 교체
# 그리고 .env에 추가:
# MAX_CONCURRENT_BATCHES=3  # 동시 처리할 배치 수 (OpenAI rate limit 고려)
