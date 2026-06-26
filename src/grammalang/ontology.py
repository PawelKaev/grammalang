from __future__ import annotations
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field, field_validator


class Substance(BaseModel):
    id: str
    name: str
    energy: float = Field(ge=0.0, le=1.0, default=0.5)


class Modus(BaseModel):
    name: str
    value: str


class Boundary(BaseModel):
    name: str
    inside: List[str] = Field(default_factory=list)
    outside: List[str] = Field(default_factory=list)


class TensionNode(BaseModel):
    id: str
    pole_a: str
    pole_b: str
    reason: str
    status: str = "held"
    resolved_at_utc: Optional[str] = None

    @field_validator("pole_a", "pole_b", mode="before")
    @classmethod
    def extract_substance_id(cls, v: Any) -> str:
        if isinstance(v, dict):
            return v.get("name", v.get("id", str(v)))
        return str(v)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v: Any) -> str:
        if isinstance(v, dict):
            return "resolved"
        return str(v).lower()


class OntologicalContext(BaseModel):
    substances: Dict[str, Substance] = Field(default_factory=dict)
    modi: Dict[str, List[Modus]] = Field(default_factory=dict)
    tensions: List[TensionNode] = Field(default_factory=list)
    boundaries: List[Boundary] = Field(default_factory=list)

    def add_substance(self, substance: Substance) -> None:
        self.substances[substance.id] = substance

    def create_tension(self, pole_a: str, pole_b: str, reason: str) -> Optional[TensionNode]:
        if pole_a not in self.substances or pole_b not in self.substances:
            return None
        node = TensionNode(
            id=f"t_{len(self.tensions)}",
            pole_a=pole_a,
            pole_b=pole_b,
            reason=reason,
        )
        self.tensions.append(node)
        return node

    def resolve_tension(self, node_id: str, winner_id: str) -> bool:
        for node in self.tensions:
            if node.id == node_id:
                if node.status != "held":
                    return False
                if winner_id not in (node.pole_a, node.pole_b):
                    return False
                node.status = "resolved"
                from datetime import datetime, timezone
                node.resolved_at_utc = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> OntologicalContext:
        return cls.model_validate(data)
