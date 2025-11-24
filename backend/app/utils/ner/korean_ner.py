from transformers import pipeline

class KoreanNER:
    def __init__(self):
        # ELECTRA NER 파이프라인 로딩
        print("✅ Hugging Face ELECTRA NER 모델 로드 중...")
        from transformers import AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained("monologg/koelectra-base-v3-naver-ner")

        self.model = pipeline(
            "token-classification",
            model="monologg/koelectra-base-v3-naver-ner",
            tokenizer=self.tokenizer,
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

    # NER 분석 함수
    def detect_korean_ner(self, text: str):
        # ELECTRA 모델의 최대 토큰 길이는 512
        # 먼저 토크나이저로 길이 체크 후 필요시 자르기
        tokens = self.tokenizer.encode(text, add_special_tokens=True)

        if len(tokens) > 512:
            print(f"[WARNING] 토큰 길이 {len(tokens)}가 512를 초과하여 잘라서 분석합니다.")
            # 512 토큰으로 자르고 다시 디코딩
            truncated_tokens = tokens[:512]
            text = self.tokenizer.decode(truncated_tokens, skip_special_tokens=True)

        raw = self.model(text)
        print("[DEBUG] 원시 모델 출력:", raw)

        merged = self.merge_iob(raw)
        print("[DEBUG] 병합된 엔티티:", merged)

        # PER, LOC, ORG만 리턴 (스코어 포함)
        label_map = {"PER": "PERSON", "LOC": "LOCATION", "ORG": "ORGANIZATION"}
        results = []
        for ent in merged:
            label = label_map.get(ent["entity_group"])
            if label:
                results.append({
                    "entity_type": label,
                    "start": ent["start"],
                    "end": ent["end"],
                    "text": text[ent["start"]:ent["end"]],
                    "score": ent["score"]
                })
        return results

