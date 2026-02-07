"""
MatchResult: Outcome explícito de pattern matching.

En lugar de retornar dicts con claves arbitrarias, usamos objetos.

Objetivos:
- Explícito: Se ve qué información tiene un match
- Observable: repr() muestra estado completo
- Testeable: Fácil validar outcomes
- Type-safe: IDE autocompleta

Uso:
    result = MatchResult.success(
        intent="open_app",
        confidence=ConfidenceScore(...),
        entities={"app": "chrome"},
        pattern_used=r"\babrir\b"
    )
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from .confidence import ConfidenceScore


@dataclass(frozen=True)
class MatchResult:
    """
    Resultado de pattern matching en NLU.
    
    Atributos:
        matched: Si hubo match exitoso
        intent: Intent detectado (None si no match)
        confidence: Score de confianza con reasoning
        entities: Entities extraídos del comando
        pattern_used: Pattern regex que matcheó (para debugging)
        alternatives: Otros intents considerados
        metadata: Info adicional (timing, reglas aplicadas, etc)
    """
    matched: bool
    intent: Optional[str] = None
    confidence: Optional[ConfidenceScore] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    pattern_used: Optional[str] = None
    alternatives: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def success(
        cls,
        intent: str,
        confidence: ConfidenceScore,
        entities: Dict[str, Any] = None,
        pattern_used: str = None,
        alternatives: list = None,
        **metadata
    ) -> "MatchResult":
        """Crea MatchResult exitoso."""
        return cls(
            matched=True,
            intent=intent,
            confidence=confidence,
            entities=entities or {},
            pattern_used=pattern_used,
            alternatives=alternatives or [],
            metadata=metadata
        )
    
    @classmethod
    def no_match(cls, reason: str = "Sin patterns que matcheen") -> "MatchResult":
        """Crea MatchResult sin match."""
        return cls(
            matched=False,
            intent=None,
            confidence=None,
            entities={},
            metadata={"reason": reason}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Conversión a dict para compatibilidad."""
        data = {
            "matched": self.matched,
            "intent": self.intent,
            "entities": self.entities,
            "pattern_used": self.pattern_used,
            "alternatives": self.alternatives,
            "metadata": self.metadata
        }
        
        if self.confidence:
            data["confidence"] = self.confidence.to_dict()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MatchResult":
        """Construcción desde dict legacy."""
        confidence_data = data.get("confidence")
        confidence = None
        if confidence_data and isinstance(confidence_data, dict):
            # Reconstruir ConfidenceScore (simplificado)
            from .confidence import ConfidenceHelper
            confidence = ConfidenceHelper.from_pattern_match(
                pattern_quality=confidence_data.get("value", 0.0)
            )
        
        return cls(
            matched=data.get("matched", False),
            intent=data.get("intent"),
            confidence=confidence,
            entities=data.get("entities", {}),
            pattern_used=data.get("pattern_used"),
            alternatives=data.get("alternatives", []),
            metadata=data.get("metadata", {})
        )
    
    def __repr__(self) -> str:
        if self.matched:
            conf_str = f"{self.confidence.value:.2f}" if self.confidence else "N/A"
            return f"MatchResult(intent='{self.intent}', confidence={conf_str})"
        else:
            return "MatchResult(no_match)"
