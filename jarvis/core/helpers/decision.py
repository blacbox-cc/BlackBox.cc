"""
Decision e IntentCandidate: Objetos explícitos para razonamiento NLU.

En lugar de dicts con claves arbitrarias, usamos objetos con contratos claros.

Objetivos:
- Explícito: Se ve qué campos tiene una decisión
- Type-safe: IDE puede autocompletar, detectar errores
- Observable: repr() muestra estado completo
- Testeable: Fácil crear decisiones mock

Uso:
    candidate = IntentCandidate(
        intent="open_app",
        confidence=0.85,
        entities={"app_name": "chrome"}
    )
    
    decision = Decision.single_match(candidate, reasoning="Match directo")
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class DecisionType(Enum):
    """Tipo de decisión tomada por el NLU."""
    SINGLE_MATCH = "single_match"        # 1 candidato con confianza alta
    MULTI_MATCH = "multi_match"          # Varios candidatos con confianza similar
    LOW_CONFIDENCE = "low_confidence"    # Candidatos con confianza baja
    NO_MATCH = "no_match"                # Sin candidatos válidos
    FALLBACK = "fallback"                # Intent fallback (default)


@dataclass(frozen=True)
class IntentCandidate:
    """
    Candidato de intent extraído del NLU pipeline.
    
    Representa una hipótesis: "el usuario quiere ejecutar [intent] con [entities]".
    
    Atributos:
        intent: Nombre del intent (ej: "open_app", "get_time")
        confidence: Confianza del match [0.0 - 1.0]
        entities: Parámetros extraídos (ej: {"app_name": "chrome"})
        reasoning: Por qué se eligió este intent (opcional, para debugging)
    """
    intent: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    reasoning: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Conversión a dict para compatibilidad."""
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "entities": self.entities,
            "reasoning": self.reasoning
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IntentCandidate":
        """Construcción desde dict legacy."""
        return cls(
            intent=data.get("intent", "unknown"),
            confidence=data.get("confidence", 0.0),
            entities=data.get("entities", {}),
            reasoning=data.get("reasoning")
        )
    
    def __repr__(self) -> str:
        return f"IntentCandidate(intent='{self.intent}', confidence={self.confidence:.2f}, entities={list(self.entities.keys())})"


@dataclass(frozen=True)
class Decision:
    """
    Decisión del NLU sobre qué intent ejecutar.
    
    Representa el resultado del proceso de razonamiento:
    - Qué candidato(s) se encontraron
    - Cuál se eligió para ejecutar
    - Por qué se tomó esa decisión
    
    Atributos:
        decision_type: Tipo de decisión (SINGLE_MATCH, MULTI_MATCH, etc)
        chosen_candidate: Candidato elegido para ejecutar (None si NO_MATCH)
        all_candidates: Todos los candidatos evaluados
        reasoning: Explicación de la decisión
        metadata: Información adicional (timing, reglas aplicadas, etc)
    """
    decision_type: DecisionType
    chosen_candidate: Optional[IntentCandidate]
    all_candidates: List[IntentCandidate] = field(default_factory=list)
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def single_match(cls, candidate: IntentCandidate, reasoning: str = "") -> "Decision":
        """Decisión con un único candidato de alta confianza."""
        return cls(
            decision_type=DecisionType.SINGLE_MATCH,
            chosen_candidate=candidate,
            all_candidates=[candidate],
            reasoning=reasoning or f"Match directo para '{candidate.intent}' con confianza {candidate.confidence:.2f}"
        )
    
    @classmethod
    def no_match(cls, reasoning: str = "Sin candidatos válidos") -> "Decision":
        """Decisión cuando no hay candidatos válidos."""
        return cls(
            decision_type=DecisionType.NO_MATCH,
            chosen_candidate=None,
            all_candidates=[],
            reasoning=reasoning
        )
    
    @classmethod
    def low_confidence(cls, candidates: List[IntentCandidate], reasoning: str = "") -> "Decision":
        """Decisión cuando todos los candidatos tienen confianza baja."""
        best = max(candidates, key=lambda c: c.confidence) if candidates else None
        return cls(
            decision_type=DecisionType.LOW_CONFIDENCE,
            chosen_candidate=best,
            all_candidates=candidates,
            reasoning=reasoning or f"Confianza baja: mejor candidato es '{best.intent}' con {best.confidence:.2f}"
        )
    
    @classmethod
    def multi_match(cls, candidates: List[IntentCandidate], chosen: IntentCandidate, reasoning: str = "") -> "Decision":
        """Decisión cuando hay múltiples candidatos con confianza similar."""
        return cls(
            decision_type=DecisionType.MULTI_MATCH,
            chosen_candidate=chosen,
            all_candidates=candidates,
            reasoning=reasoning or f"Múltiples candidatos, elegido '{chosen.intent}'"
        )
    
    @classmethod
    def fallback(cls, reasoning: str = "Intent fallback aplicado") -> "Decision":
        """Decisión cuando se usa intent fallback."""
        fallback_candidate = IntentCandidate(
            intent="fallback",
            confidence=1.0,
            reasoning="Intent por defecto"
        )
        return cls(
            decision_type=DecisionType.FALLBACK,
            chosen_candidate=fallback_candidate,
            all_candidates=[fallback_candidate],
            reasoning=reasoning
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Conversión a dict para compatibilidad."""
        return {
            "decision_type": self.decision_type.value,
            "chosen_candidate": self.chosen_candidate.to_dict() if self.chosen_candidate else None,
            "all_candidates": [c.to_dict() for c in self.all_candidates],
            "reasoning": self.reasoning,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Decision":
        """Construcción desde dict legacy."""
        decision_type = DecisionType(data.get("decision_type", "single_match"))
        chosen_data = data.get("chosen_candidate")
        chosen_candidate = IntentCandidate.from_dict(chosen_data) if chosen_data else None
        all_candidates = [
            IntentCandidate.from_dict(c)
            for c in data.get("all_candidates", [])
        ]
        return cls(
            decision_type=decision_type,
            chosen_candidate=chosen_candidate,
            all_candidates=all_candidates,
            reasoning=data.get("reasoning", ""),
            metadata=data.get("metadata", {})
        )
    
    def __repr__(self) -> str:
        intent_name = self.chosen_candidate.intent if self.chosen_candidate else "None"
        return f"Decision({self.decision_type.value}, intent='{intent_name}')"
