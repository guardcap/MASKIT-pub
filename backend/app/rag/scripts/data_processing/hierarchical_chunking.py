"""
계층적 청킹 (Hierarchical Chunking) 스크립트

문제점:
- "1. 정보주체의 동의를 받은 경우" 같은 하위 조항 청크만으로는 맥락 파악 불가
- 상위 조항 정보 (제15조, 개인정보의 수집·이용 허용 조건) 없이는 의미 해석 불가

해결책:
- 각 청크에 상위 맥락(법률명, 조, 항, 호)을 포함하여 저장
- 예: "[법률: 개인정보보호법][제15조(개인정보의 수집ㆍ이용)] ① ...개인정보를 수집 및 이용할 수 있다. [1호] 정보주체의 동의를 받은 경우"

입력:
- C_laws.jsonl: 법률 조항 데이터
- B_policies.jsonl: 정책 규정 데이터

출력:
- C_laws_hierarchical.jsonl
- B_policies_hierarchical.jsonl
"""

import json
import os
from collections import defaultdict
from typing import Dict, List, Optional


class HierarchicalChunker:
    """법률/정책 문서를 계층적 맥락을 포함한 청크로 변환"""

    def __init__(self):
        self.law_articles = defaultdict(dict)
        self.law_clauses_by_article = defaultdict(list)

    def _build_hierarchical_text_for_laws(self, doc: Dict) -> str:
        """법률 문서에 대해 계층적 맥락을 포함한 전체 텍스트 생성"""
        law_name = doc.get("law_name", "")
        article_num = doc.get("article_num", "")
        article_title = doc.get("article_title", "")
        clause_num = doc.get("clause_num", "")
        content = doc.get("content", "")

        base = f"[법률: {law_name}][{article_num}({article_title})]"

        if not clause_num:
            return f"{base} {content}"

        parent_docs = [
            d for d in self.law_clauses_by_article.get(article_num, [])
            if not d.get("clause_num")
        ]

        if not parent_docs:
            parent_docs = [
                d for d in self.law_clauses_by_article.get(article_num, [])
                if d.get("clause_num") == "1항"
            ]

        if parent_docs:
            parent = parent_docs[0]
            parent_content = parent.get("content", "")
            parent_summary = parent_content[:100] + "..." if len(parent_content) > 100 else parent_content
            return f"{base} **[상위 조항]** {parent_summary}\n\n**[{clause_num}]** {content}"
        else:
            return f"{base} **[{clause_num}]** {content}"

    def _build_hierarchical_text_for_policies(self, doc: Dict) -> str:
        """정책 문서에 대해 계층적 맥락을 포함한 전체 텍스트 생성"""
        policy_id = doc.get("policy_id", "")
        content = doc.get("content", "")

        parts = policy_id.split("-")
        if len(parts) >= 5:
            policy_name = parts[2]
            article_num = parts[3]
            sub_num = parts[4]
            return f"[정책: {policy_name}][제{article_num}조] **[{sub_num}]** {content}"

        return f"[정책] {content}"

    def process_laws(self, input_file: str, output_file: str):
        """법률 파일(C_laws.jsonl)을 계층적 청킹으로 변환"""
        print(f"\n📄 법률 파일 처리 시작: {input_file}")

        all_docs = []
        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                doc = json.loads(line)
                all_docs.append(doc)
                article_num = doc.get("article_num")
                clause_num = doc.get("clause_num")
                if not clause_num:
                    self.law_articles[article_num] = doc
                self.law_clauses_by_article[article_num].append(doc)

        print(f"   - 총 {len(all_docs)}개 문서 로드 완료")
        print(f"   - {len(self.law_articles)}개 조(article) 발견")

        processed_count = 0
        with open(output_file, "w", encoding="utf-8") as out_f:
            for doc in all_docs:
                new_doc = doc.copy()
                hierarchical_text = self._build_hierarchical_text_for_laws(doc)
                new_doc["hierarchical_text"] = hierarchical_text
                new_doc["text_column"] = hierarchical_text
                out_f.write(json.dumps(new_doc, ensure_ascii=False) + "\n")
                processed_count += 1

        print(f"   - ✅ {processed_count}개 문서 처리 완료")
        print(f"   - 출력 파일: {output_file}\n")

    def process_policies(self, input_file: str, output_file: str):
        """정책 파일(B_policies.jsonl)을 계층적 청킹으로 변환"""
        print(f"\n📄 정책 파일 처리 시작: {input_file}")

        processed_count = 0
        with open(input_file, "r", encoding="utf-8") as in_f, open(output_file, "w", encoding="utf-8") as out_f:
            for line in in_f:
                doc = json.loads(line)
                new_doc = doc.copy()
                hierarchical_text = self._build_hierarchical_text_for_policies(doc)
                new_doc["hierarchical_text"] = hierarchical_text
                new_doc["text_column"] = hierarchical_text
                out_f.write(json.dumps(new_doc, ensure_ascii=False) + "\n")
                processed_count += 1

        print(f"   - ✅ {processed_count}개 문서 처리 완료")
        print(f"   - 출력 파일: {output_file}\n")


def main():
    """메인 실행 함수"""
    print("\n" + "="*80)
    print(" 계층적 청킹 (Hierarchical Chunking) 프로세스 시작 ".center(80, "="))
    print("="*80)

    BASE_DIR = "./data/staging"
    INPUT_LAWS = os.path.join(BASE_DIR, "C_laws.jsonl")
    INPUT_POLICIES = os.path.join(BASE_DIR, "B_policies.jsonl")
    OUTPUT_LAWS = os.path.join(BASE_DIR, "C_laws_hierarchical.jsonl")
    OUTPUT_POLICIES = os.path.join(BASE_DIR, "B_policies_hierarchical.jsonl")

    if not os.path.exists(INPUT_LAWS):
        print(f"❌ 오류: 법률 파일을 찾을 수 없습니다: {INPUT_LAWS}")
        return

    if not os.path.exists(INPUT_POLICIES):
        print(f"❌ 오류: 정책 파일을 찾을 수 없습니다: {INPUT_POLICIES}")
        return

    chunker = HierarchicalChunker()
    chunker.process_laws(INPUT_LAWS, OUTPUT_LAWS)
    chunker.process_policies(INPUT_POLICIES, OUTPUT_POLICIES)

    print("="*80)
    print(" 계층적 청킹 프로세스 완료 ".center(80, "="))
    print("="*80)

    print("\n📊 결과 요약:")
    print(f"   - 법률 출력: {OUTPUT_LAWS}")
    print(f"   - 정책 출력: {OUTPUT_POLICIES}")

    print("\n✨ 다음 단계:")
    print("   1. 출력 파일 내용을 확인하세요")
    print("   2. ChromaDB 인덱스를 재구축하세요:")
    print("      python scripts/hybrid/build_chromadb.py")
    print("\n")

    print("\n📋 샘플 출력 (법률 - 처음 3개 항목):")
    print("-" * 80)
    with open(OUTPUT_LAWS, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 3:
                break
            doc = json.loads(line)
            print(f"\n[{i+1}] ID: {doc.get('law_id')}")
            print(f"    Hierarchical Text:\n    {doc.get('hierarchical_text', '')[:200]}...")

    print("\n" + "-" * 80)


if __name__ == "__main__":
    main()
