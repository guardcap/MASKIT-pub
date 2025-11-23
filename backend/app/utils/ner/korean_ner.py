from transformers import pipeline
import re

class KoreanNER:
    MAX_LENGTH = 512  # ELECTRA 모델 최대 토큰 길이
    CHUNK_SIZE = 400  # 청크 크기 (여유분 확보)

    def __init__(self):
        # ELECTRA NER 파이프라인 로딩
        print("✅ Hugging Face ELECTRA NER 모델 로드 중...")
        self.model = pipeline(
            "token-classification",
            model="monologg/koelectra-base-v3-naver-ner",
            aggregation_strategy="none",
        )

        # id2label 교정 (PER-B → B-PER 등)
        hf_model = self.model.model
        orig_id2label = hf_model.config.id2label
        new_id2label = {}
        for idx, lbl in orig_id2label.items():
            if lbl.endswith("-B") or lbl.endswith("-I"):
                ent, tag = lbl.split("-", 1)
                new_id2label[int(idx)] = f"{tag}-{ent}"
            else:
                new_id2label[int(idx)] = lbl
        hf_model.config.id2label = new_id2label
        hf_model.config.label2id = {v: k for k, v in new_id2label.items()}
        print("✅ 모델 준비 완료 (id2label 교정 완료)")

    # IOB 병합 함수
    def merge_iob(self, tokens):
        merged = []
        cur = None
        for t in tokens:
            iob = t.get("entity")
            if not iob or iob == "O":
                if cur:
                    merged.append(cur)
                    cur = None
                continue
            tag, grp = iob.split("-", 1)
            word = t.get("word", "")
            is_sub = word.startswith("##")
            clean = word[2:] if is_sub else word

            if cur and cur["entity_group"] == grp and (tag == "I" or (tag == "B" and is_sub)):
                cur["end"] = t["end"]
                cur["word"] += clean
                cur["score"] = min(cur["score"], float(t.get("score", 0.0)))
            elif tag == "B" and not is_sub:
                if cur:
                    merged.append(cur)
                cur = {
                    "entity_group": grp,
                    "start": t["start"],
                    "end": t["end"],
                    "word": clean,
                    "score": float(t.get("score", 0.0))
                }
            else:
                if cur:
                    merged.append(cur)
                cur = {
                    "entity_group": grp,
                    "start": t["start"],
                    "end": t["end"],
                    "word": clean,
                    "score": float(t.get("score", 0.0))
                }
        if cur:
            merged.append(cur)
        return merged

    # 텍스트를 청크로 분할
    def _split_into_chunks(self, text: str):
        """긴 텍스트를 청크로 분할 (문장 단위로 끊어서)"""
        if len(text) <= self.CHUNK_SIZE:
            return [(0, text)]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.CHUNK_SIZE
            if end >= len(text):
                chunks.append((start, text[start:]))
                break

            # 문장 끝 또는 공백에서 끊기
            split_pos = end
            for sep in ['. ', '.\n', '? ', '! ', '\n', ' ']:
                pos = text[start:end].rfind(sep)
                if pos > 0:
                    split_pos = start + pos + len(sep)
                    break

            chunks.append((start, text[start:split_pos]))
            start = split_pos

        return chunks

    # NER 분석 함수
# backend/app/utils/ner/korean_ner.py
# detect_korean_ner 함수 수정:

    def detect_korean_ner(self, text: str):
        chunks = self._split_into_chunks(text)
        all_merged = []

        for offset, chunk in chunks:
            try:
                raw = self.model(chunk, truncation=True, max_length=self.MAX_LENGTH)
                merged = self.merge_iob(raw)

                # offset 적용하여 원본 텍스트 위치로 변환
                for ent in merged:
                    ent["start"] += offset
                    ent["end"] += offset
                    all_merged.append(ent)
            except Exception as e:
                print(f"[WARN] NER 청크 처리 실패 (offset={offset}): {e}")
                continue

        print(f"[DEBUG] 총 {len(chunks)}개 청크에서 {len(all_merged)}개 엔티티 발견")

        # PER, LOC, ORG만 리턴 (스코어 포함)
        label_map = {"PER": "PERSON", "LOC": "LOCATION", "ORG": "ORGANIZATION"}
        results = []
        for ent in all_merged:
            label = label_map.get(ent["entity_group"])
            if label:
                entity_text = text[ent["start"]:ent["end"]]
                
                # ===== 필터링 로직 추가 =====
                # 1. 괄호만 있는 경우 제외
                if entity_text.strip() in ['(', ')', '()', '( )', '[]', '{}','<','>']:
                    print(f"[DEBUG] 괄호 필터링: '{entity_text}'")
                    continue
                
                # 2. 괄호로만 구성된 경우 제외
                if re.match(r'^[\(\)\[\]\{\}\s]*$', entity_text):
                    print(f"[DEBUG] 괄호 패턴 필터링: '{entity_text}'")
                    continue
                
                # 3. LOC인데 길이가 1자 이하인 경우 제외
                if label == "LOCATION" and len(entity_text.strip()) <= 1:
                    print(f"[DEBUG] 짧은 LOC 필터링: '{entity_text}'")
                    continue
                
                # 4. LOC인데 숫자/기호만 있는 경우 제외
                if label == "LOCATION" and re.match(r'^[\d\s\(\)\[\]\{\}\-\.,;:]+$', entity_text):
                    print(f"[DEBUG] 숫자/기호만 있는 LOC 필터링: '{entity_text}'")
                    continue
                # ===========================
                
                results.append({
                    "entity_type": label,
                    "start": ent["start"],
                    "end": ent["end"],
                    "text": entity_text,
                    "score": ent["score"]
                })
        return results

