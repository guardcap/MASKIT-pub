from typing import List, Dict, Any
from collections import defaultdict
from typing import Tuple

class Entity:
    def __init__(
        self,
        entity: str,
        score: float,
        word: str,
        start: int,
        end: int,
        pageIndex: int = None,
        bbox: Tuple[int, int, int, int] = None
    ):
        self.entity = entity                # 엔티티 종류 (예: "EMAIL", "NAME")
        self.score = score                  # 신뢰도 점수
        self.word = word                    # 인식된 단어 또는 텍스트
        self.start = start                  # 텍스트 내 시작 인덱스
        self.end = end                      # 텍스트 내 끝 인덱스
        self.pageIndex = pageIndex          # 해당 OCR 페이지 번호
        self.bbox = bbox                    # Bounding Box (x1, y1, x2, y2)

    def __repr__(self):
        return (
            f"Entity(entity='{self.entity}', score={self.score:.2f}, "
            f"word='{self.word}', start={self.start}, end={self.end}, "
            f"pageIndex={self.pageIndex}, bbox={self.bbox})"
        )

    def to_dict(self):
        return {
            "entity": self.entity,
            "score": self.score,
            "word": self.word,
            "start": self.start,
            "end": self.end,
            "pageIndex": self.pageIndex,
            "bbox": self.bbox,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            entity=data.get("entity"),
            score=data.get("score"),
            word=data.get("word"),
            start=data.get("start"),
            end=data.get("end"),
            pageIndex=data.get("pageIndex"),
            bbox=tuple(data["bbox"]) if data.get("bbox") else None
        )


class EntityGroup:
    def __init__(self, entities: List[Entity] = None):
        self.entities: List[Entity] = entities if entities else []

    def add_entity(self, entity: Entity):
        self.entities.append(entity)

    def remove_entity(self, entity: Entity):
        self.entities.remove(entity)

    def filter_by_type(self, entity_type: str) -> List[Entity]:
        return [e for e in self.entities if e.entity == entity_type]

    def group_by_page(self) -> Dict[int, List[Entity]]:
        grouped = defaultdict(list)
        for e in self.entities:
            if e.pageIndex is not None:
                grouped[e.pageIndex].append(e)
        return dict(grouped)

    def to_dict(self) -> List[Dict[str, Any]]:
        return [entity.to_dict() for entity in self.entities]

    @classmethod
    def from_dict(cls, data: List[Dict[str, Any]]):
        entities = [Entity.from_dict(item) for item in data]
        return cls(entities)

    def __repr__(self):
        return f"EntityGroup(total={len(self.entities)} entities)"

