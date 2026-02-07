"""
ConfidenceHelper: Cálculos explícitos de confianza para NLU.

En lugar de números mágicos (0.6, 0.8, etc), usamos funciones con nombres claros.

Objetivos:
- Explícito: Se ve por qué un match tiene X confianza
- Observable: Logs muestran reglas aplicadas
- Testeable: Fácil validar cálculos
- Ajustable: Cambiar thresholds sin tocar código disperso

Uso:
    confidence = ConfidenceHelper.from_pattern_match(
        pattern_quality=0.8,
        entity_match=0.9
    )
    
    if ConfidenceHelper.is_high_confidence(confidence):
        # Ejecutar directamente
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class ConfidenceLevel(Enum):
    """Niveles de confianza semánticos."""
    VERY_HIGH = "very_high"    # >= 0.9: Ejecutar sin confirmación
    HIGH = "high"               # >= 0.7: Ejecutar, pero loggear alternativas
    MEDIUM = "medium"           # >= 0.5: Mostrar alternativas al usuario
    LOW = "low"                 # >= 0.3: Sugerir reformular comando
    VERY_LOW = "very_low"       # < 0.3: No ejecutar, pedir clarificación


@dataclass(frozen=True)
class ConfidenceScore:
    """
    Score de confianza con metadata explicativa.
    
    Atributos:
        value: Score numérico [0.0 - 1.0]
        level: Nivel semántico (HIGH, MEDIUM, etc)
        reasoning: Por qué se asignó este score
        components: Descomposición del cálculo (pattern=0.8, entity=0.9, etc)
    """
    value: float
    level: ConfidenceLevel
    reasoning: str = ""
    components: Dict[str, float] = None
    
    def __post_init__(self):
        # Validar range
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Confidence debe estar en [0.0, 1.0], recibido: {self.value}")
        
        # Default components
        if self.components is None:
            object.__setattr__(self, 'components', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Conversión a dict para logs."""
        return {
            "value": round(self.value, 3),
            "level": self.level.value,
            "reasoning": self.reasoning,
            "components": self.components
        }
    
    def __repr__(self) -> str:
        return f"ConfidenceScore(value={self.value:.2f}, level={self.level.value})"
    
    def __float__(self) -> float:
        """Permite usar como float: if confidence > 0.8"""
        return self.value


class ConfidenceHelper:
    """
    Helper para cálculos de confianza explícitos.
    
    En lugar de:
        confidence = 0.8  # ¿Por qué 0.8? ¿Qué significa?
    
    Usamos:
        confidence = ConfidenceHelper.from_pattern_match(...)
        # Reasoning explícito, componentes visibles
    """
    
    # Thresholds configurables
    THRESHOLD_VERY_HIGH = 0.9
    THRESHOLD_HIGH = 0.7
    THRESHOLD_MEDIUM = 0.5
    THRESHOLD_LOW = 0.3
    
    @classmethod
    def from_pattern_match(
        cls,
        pattern_quality: float,
        entity_match: Optional[float] = None,
        context_boost: float = 0.0,
        penalty: float = 0.0
    ) -> ConfidenceScore:
        """
        Calcula confianza desde pattern matching.
        
        Args:
            pattern_quality: Calidad del match regex [0.0 - 1.0]
            entity_match: Calidad de entities extraídos (opcional)
            context_boost: Boost por contexto/historia [0.0 - 0.2]
            penalty: Penalización por ambigüedad [-0.5 - 0.0]
        
        Returns:
            ConfidenceScore con reasoning explícito
        """
        # Calcular base
        if entity_match is not None:
            base = (pattern_quality + entity_match) / 2.0
        else:
            base = pattern_quality
        
        # Aplicar boost y penalty
        value = max(0.0, min(1.0, base + context_boost + penalty))
        
        # Determinar level
        level = cls._value_to_level(value)
        
        # Construir reasoning
        components = {
            "pattern_quality": pattern_quality,
        }
        if entity_match is not None:
            components["entity_match"] = entity_match
        if context_boost != 0.0:
            components["context_boost"] = context_boost
        if penalty != 0.0:
            components["penalty"] = penalty
        
        reasoning_parts = [f"Pattern match: {pattern_quality:.2f}"]
        if entity_match is not None:
            reasoning_parts.append(f"Entity match: {entity_match:.2f}")
        if context_boost > 0:
            reasoning_parts.append(f"Context boost: +{context_boost:.2f}")
        if penalty < 0:
            reasoning_parts.append(f"Ambiguity penalty: {penalty:.2f}")
        
        reasoning = " | ".join(reasoning_parts)
        
        return ConfidenceScore(
            value=value,
            level=level,
            reasoning=reasoning,
            components=components
        )
    
    @classmethod
    def from_soft_match(
        cls,
        similarity: float,
        threshold: float = 0.8,
        matched_tokens: int = 0,
        total_tokens: int = 1
    ) -> ConfidenceScore:
        """
        Calcula confianza desde soft phrase matching.
        
        Args:
            similarity: Similaridad calculada [0.0 - 1.0]
            threshold: Threshold usado para considerar match
            matched_tokens: Número de tokens matcheados
            total_tokens: Total de tokens en query
        """
        # Ajustar por coverage de tokens
        coverage = matched_tokens / total_tokens if total_tokens > 0 else 0.0
        value = similarity * (0.7 + 0.3 * coverage)  # Bonus por coverage alto
        
        level = cls._value_to_level(value)
        
        reasoning = f"Similarity: {similarity:.2f} (threshold={threshold:.2f}), Coverage: {matched_tokens}/{total_tokens}"
        
        return ConfidenceScore(
            value=value,
            level=level,
            reasoning=reasoning,
            components={
                "similarity": similarity,
                "coverage": coverage,
                "threshold": threshold
            }
        )
    
    @classmethod
    def from_multiple_candidates(
        cls,
        top_score: float,
        second_score: float,
        gap_threshold: float = 0.15
    ) -> ConfidenceScore:
        """
        Ajusta confianza cuando hay múltiples candidatos.
        
        Si hay candidatos muy cercanos, reduce confianza (ambigüedad).
        
        Args:
            top_score: Score del mejor candidato
            second_score: Score del segundo mejor
            gap_threshold: Gap mínimo para considerar claro (default: 0.15)
        """
        gap = top_score - second_score
        
        if gap >= gap_threshold:
            # Gap claro: mantener top_score
            value = top_score
            reasoning = f"Clear winner: gap={gap:.2f} >= {gap_threshold}"
        else:
            # Gap pequeño: penalizar por ambigüedad
            penalty = (gap_threshold - gap) * 0.5  # Max penalty: -0.075
            value = max(0.0, top_score - penalty)
            reasoning = f"Ambiguous: gap={gap:.2f} < {gap_threshold}, penalty={penalty:.2f}"
        
        level = cls._value_to_level(value)
        
        return ConfidenceScore(
            value=value,
            level=level,
            reasoning=reasoning,
            components={
                "top_score": top_score,
                "second_score": second_score,
                "gap": gap,
                "gap_threshold": gap_threshold
            }
        )
    
    @classmethod
    def combine(
        cls,
        *scores: ConfidenceScore,
        method: str = "average"
    ) -> ConfidenceScore:
        """
        Combina múltiples scores.
        
        Args:
            scores: Scores a combinar
            method: "average", "min", "max", "weighted"
        """
        if not scores:
            return cls.zero(reasoning="No scores to combine")
        
        values = [s.value for s in scores]
        
        if method == "average":
            value = sum(values) / len(values)
        elif method == "min":
            value = min(values)
        elif method == "max":
            value = max(values)
        else:
            value = sum(values) / len(values)  # Default to average
        
        level = cls._value_to_level(value)
        reasoning = f"Combined {len(scores)} scores using {method}: {[f'{v:.2f}' for v in values]}"
        
        return ConfidenceScore(
            value=value,
            level=level,
            reasoning=reasoning,
            components={"method": method, "input_scores": values}
        )
    
    @classmethod
    def zero(cls, reasoning: str = "No match") -> ConfidenceScore:
        """Confidence score de 0 (sin match)."""
        return ConfidenceScore(
            value=0.0,
            level=ConfidenceLevel.VERY_LOW,
            reasoning=reasoning
        )
    
    @classmethod
    def perfect(cls, reasoning: str = "Exact match") -> ConfidenceScore:
        """Confidence score de 1.0 (match perfecto)."""
        return ConfidenceScore(
            value=1.0,
            level=ConfidenceLevel.VERY_HIGH,
            reasoning=reasoning
        )
    
    @classmethod
    def _value_to_level(cls, value: float) -> ConfidenceLevel:
        """Convierte valor numérico a nivel semántico."""
        if value >= cls.THRESHOLD_VERY_HIGH:
            return ConfidenceLevel.VERY_HIGH
        elif value >= cls.THRESHOLD_HIGH:
            return ConfidenceLevel.HIGH
        elif value >= cls.THRESHOLD_MEDIUM:
            return ConfidenceLevel.MEDIUM
        elif value >= cls.THRESHOLD_LOW:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    @classmethod
    def is_very_high(cls, score: ConfidenceScore) -> bool:
        """¿Es confianza muy alta? (>= 0.9)"""
        return score.level == ConfidenceLevel.VERY_HIGH
    
    @classmethod
    def is_high_confidence(cls, score: ConfidenceScore) -> bool:
        """¿Es confianza alta o muy alta? (>= 0.7)"""
        return score.level in (ConfidenceLevel.VERY_HIGH, ConfidenceLevel.HIGH)
    
    @classmethod
    def is_actionable(cls, score: ConfidenceScore) -> bool:
        """¿Es suficiente confianza para ejecutar? (>= 0.5)"""
        return score.value >= cls.THRESHOLD_MEDIUM
    
    @classmethod
    def needs_clarification(cls, score: ConfidenceScore) -> bool:
        """¿Necesita clarificación del usuario? (< 0.5)"""
        return score.value < cls.THRESHOLD_MEDIUM
