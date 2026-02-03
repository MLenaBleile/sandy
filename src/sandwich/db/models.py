"""Pydantic models for the SANDWICH database entities."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Source(BaseModel):
    source_id: UUID = Field(default_factory=uuid4)
    url: Optional[str] = None
    domain: Optional[str] = None
    content: Optional[str] = None
    content_hash: Optional[str] = None
    fetched_at: datetime = Field(default_factory=datetime.now)
    content_type: Optional[str] = None


class StructuralType(BaseModel):
    type_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    bread_relation: Optional[str] = None
    filling_role: Optional[str] = None
    parent_type_id: Optional[int] = None
    canonical_example_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Sandwich(BaseModel):
    sandwich_id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    validity_score: Optional[float] = None
    bread_compat_score: Optional[float] = None
    containment_score: Optional[float] = None
    specificity_score: Optional[float] = None
    nontrivial_score: Optional[float] = None
    novelty_score: Optional[float] = None

    bread_top: str
    bread_bottom: str
    filling: str

    source_id: Optional[UUID] = None
    structural_type_id: Optional[int] = None
    assembly_rationale: Optional[str] = None
    validation_rationale: Optional[str] = None
    reuben_commentary: Optional[str] = None


class Ingredient(BaseModel):
    ingredient_id: UUID = Field(default_factory=uuid4)
    text: str
    ingredient_type: str  # 'bread' or 'filling'
    first_seen_sandwich: Optional[UUID] = None
    first_seen_at: datetime = Field(default_factory=datetime.now)
    usage_count: int = 1


class SandwichIngredient(BaseModel):
    sandwich_id: UUID
    ingredient_id: UUID
    role: str  # 'bread_top', 'bread_bottom', 'filling'


class SandwichRelation(BaseModel):
    relation_id: UUID = Field(default_factory=uuid4)
    sandwich_a: UUID
    sandwich_b: UUID
    relation_type: str
    similarity_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)
    rationale: Optional[str] = None


class ForagingLogEntry(BaseModel):
    log_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.now)
    source_id: Optional[UUID] = None
    curiosity_prompt: Optional[str] = None
    outcome: Optional[str] = None
    outcome_rationale: Optional[str] = None
    sandwich_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
