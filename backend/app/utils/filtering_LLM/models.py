from __future__ import annotations
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field
from ..entity import Entity, EntityGroup

# 타입 라벨
SourceType = Literal["LAW", "GOV_GUIDE", "INTERNAL_POLICY", "CONTRACT"]
Audience   = Literal["external", "internal_public", "internal_limited"]
Redact     = Literal["keep", "mask_partial", "mask_full", "generalize", "pseudonymize", "tokenize", "hash"]

class Meta(BaseModel):
    sender_team: str
    sender_role: str
    recipient_domain: str
    recipient_role: Optional[str] = None
    purpose: str
    audience: Audience
    jurisdiction: str = "KR"

class Span(BaseModel):
    id: str
    type: str              # Entity.entity와 매핑
    text: str             # Entity.word와 매핑
    page: Optional[int] = None  # Entity.pageIndex와 매핑
    start: Optional[int] = None  # Entity.start와 매핑
    end: Optional[int] = None    # Entity.end와 매핑
    bbox: Optional[List[float]] = None  # Entity.bbox와 매핑
    confidence: Optional[float] = None   # Entity.score와 매핑

    @classmethod
    def from_entity(cls, entity_id: str, entity: 'Entity') -> 'Span':
        return cls(
            id=entity_id,
            type=entity.entity,
            text=entity.word,
            page=entity.pageIndex,
            start=entity.start,
            end=entity.end,
            bbox=list(entity.bbox) if entity.bbox else None,
            confidence=entity.score
        )

class RuleChunk(BaseModel):
    # 규정 "청크" 단위 저장 (문맥적으로 동일한 최소 문단/문장 묶음)
    chunk_id: str
    cluster_id: str
    doc_id: str
    source_type: SourceType

    jurisdiction: str
    audience: List[str] = Field(default_factory=lambda: ["any"])
    role_scope: List[str] = Field(default_factory=lambda: ["all"])

    data_types: List[str] = Field(default_factory=list)
    action_scope: List[str] = Field(default_factory=list)

    priority_base: float = 0.0
    text: str

    # 필요시 확장: effective_start/end, lineage, exceptions 등

class ContextPack(BaseModel):
    # RAG 결과: 청크 중심 컨텍스트 팩
    chunks: List[RuleChunk] = Field(default_factory=list)
    clusters: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)

class MaskingAction:
    """마스킹 결정을 Entity에 적용하는 헬퍼 클래스"""
    @staticmethod
    def apply_decision(entity: Entity, decision: Redact, format_options: Dict[str, Any] = None) -> Entity:
        # 원본 엔티티 정보 복사
        masked_entity = Entity(
            entity=entity.entity,
            score=entity.score,
            word=entity.word,  # 실제 마스킹은 나중에 masking_engine에서 수행
            start=entity.start,
            end=entity.end,
            pageIndex=entity.pageIndex,
            bbox=entity.bbox
        )
        # 마스킹 메타데이터 추가
        masked_entity.masking_method = decision  # type: ignore
        if format_options:
            masked_entity.masking_format = format_options  # type: ignore
        return masked_entity
