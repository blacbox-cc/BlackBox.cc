"""
DecisionPolicy: Reglas explícitas para tomar decisiones NLU.

En lugar de lógica dispersa en if/else, centralizamos policies configurables.

Objetivos:
- Explícito: Se ve qué reglas se aplicaron
- Observable: Logs muestran reasoning de cada policy
- Testeable: Fácil probar cada policy aisladamente
- Configurable: Cambiar thresholds sin tocar código

Uso:
    policy = ConfidenceThresholdPolicy(threshold=0.7)
    result = policy.apply(candidates)
    
    if result.approved:
        execute(result.chosen_candidate)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from .decision import IntentCandidate, Decision, DecisionType
from .confidence import ConfidenceScore, ConfidenceHelper


class PolicyDecision(Enum):
    """Resultado de aplicar una policy."""
    APPROVE = "approve"          # Aprobar ejecución
    REJECT = "reject"            # Rechazar ejecución
    CLARIFY = "clarify"          # Pedir clarificación al usuario
    DEFER = "defer"              # Diferir a otra policy


@dataclass(frozen=True)
class PolicyResult:
    """
    Resultado de aplicar una DecisionPolicy.
    
    Atributos:
        decision: APPROVE, REJECT, CLARIFY, DEFER
        chosen_candidate: Candidato elegido (si APPROVE)
        reasoning: Por qué se tomó esta decisión
        metadata: Info adicional (threshold usado, alternativas, etc)
    """
    decision: PolicyDecision
    chosen_candidate: Optional[IntentCandidate] = None
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def approved(self) -> bool:
        """¿La policy aprobó ejecución?"""
        return self.decision == PolicyDecision.APPROVE
    
    @property
    def rejected(self) -> bool:
        """¿La policy rechazó ejecución?"""
        return self.decision == PolicyDecision.REJECT
    
    @property
    def needs_clarification(self) -> bool:
        """¿La policy pide clarificación?"""
        return self.decision == PolicyDecision.CLARIFY
    
    def to_dict(self) -> Dict[str, Any]:
        """Conversión a dict para logs."""
        return {
            "decision": self.decision.value,
            "chosen_candidate": self.chosen_candidate.to_dict() if self.chosen_candidate else None,
            "reasoning": self.reasoning,
            "metadata": self.metadata
        }
    
    def __repr__(self) -> str:
        intent = self.chosen_candidate.intent if self.chosen_candidate else "None"
        return f"PolicyResult({self.decision.value}, intent='{intent}')"


class DecisionPolicy:
    """
    Base class para policies de decisión.
    
    Subclases implementan apply() con lógica específica.
    """
    
    def apply(self, candidates: List[IntentCandidate]) -> PolicyResult:
        """
        Aplica policy a lista de candidatos.
        
        Args:
            candidates: Lista de IntentCandidates
        
        Returns:
            PolicyResult con decisión tomada
        """
        raise NotImplementedError("Subclasses must implement apply()")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class ConfidenceThresholdPolicy(DecisionPolicy):
    """
    Policy: Aprobar solo si el mejor candidato supera threshold.
    
    Uso:
        policy = ConfidenceThresholdPolicy(threshold=0.7)
        result = policy.apply(candidates)
    """
    
    def __init__(self, threshold: float = 0.7, min_gap: float = 0.15):
        """
        Args:
            threshold: Confianza mínima para aprobar [0.0-1.0]
            min_gap: Gap mínimo vs segundo candidato (anti-ambigüedad)
        """
        self.threshold = threshold
        self.min_gap = min_gap
    
    def apply(self, candidates: List[IntentCandidate]) -> PolicyResult:
        if not candidates:
            return PolicyResult(
                decision=PolicyDecision.REJECT,
                reasoning="Sin candidatos para evaluar",
                metadata={"threshold": self.threshold}
            )
        
        # Ordenar por confianza
        sorted_candidates = sorted(candidates, key=lambda c: c.confidence, reverse=True)
        best = sorted_candidates[0]
        
        # Check threshold
        if best.confidence < self.threshold:
            return PolicyResult(
                decision=PolicyDecision.CLARIFY,
                chosen_candidate=best,
                reasoning=f"Confianza {best.confidence:.2f} < threshold {self.threshold}",
                metadata={
                    "threshold": self.threshold,
                    "best_confidence": best.confidence,
                    "alternatives": [c.intent for c in sorted_candidates[:3]]
                }
            )
        
        # Check ambigüedad (gap con segundo)
        if len(sorted_candidates) > 1:
            second = sorted_candidates[1]
            gap = best.confidence - second.confidence
            
            if gap < self.min_gap:
                return PolicyResult(
                    decision=PolicyDecision.CLARIFY,
                    chosen_candidate=best,
                    reasoning=f"Ambiguo: gap {gap:.2f} < {self.min_gap} (segundo: {second.intent})",
                    metadata={
                        "best": best.intent,
                        "second": second.intent,
                        "gap": gap,
                        "min_gap": self.min_gap
                    }
                )
        
        # Todo OK: aprobar
        return PolicyResult(
            decision=PolicyDecision.APPROVE,
            chosen_candidate=best,
            reasoning=f"Confianza {best.confidence:.2f} >= {self.threshold}, gap claro",
            metadata={
                "confidence": best.confidence,
                "threshold": self.threshold
            }
        )
    
    def __repr__(self) -> str:
        return f"ConfidenceThresholdPolicy(threshold={self.threshold}, min_gap={self.min_gap})"


class SingleCandidatePolicy(DecisionPolicy):
    """
    Policy: Aprobar solo si hay un único candidato con confianza suficiente.
    
    Útil para comandos críticos donde la ambigüedad es inaceptable.
    """
    
    def __init__(self, min_confidence: float = 0.8):
        self.min_confidence = min_confidence
    
    def apply(self, candidates: List[IntentCandidate]) -> PolicyResult:
        valid_candidates = [c for c in candidates if c.confidence >= self.min_confidence]
        
        if len(valid_candidates) == 0:
            return PolicyResult(
                decision=PolicyDecision.REJECT,
                reasoning=f"Sin candidatos con confianza >= {self.min_confidence}",
                metadata={"min_confidence": self.min_confidence}
            )
        
        if len(valid_candidates) > 1:
            return PolicyResult(
                decision=PolicyDecision.CLARIFY,
                reasoning=f"Múltiples candidatos válidos ({len(valid_candidates)}): ambigüedad",
                metadata={
                    "valid_candidates": [c.intent for c in valid_candidates],
                    "min_confidence": self.min_confidence
                }
            )
        
        # Exactamente 1 candidato válido
        return PolicyResult(
            decision=PolicyDecision.APPROVE,
            chosen_candidate=valid_candidates[0],
            reasoning=f"Único candidato válido: {valid_candidates[0].intent}",
            metadata={"confidence": valid_candidates[0].confidence}
        )
    
    def __repr__(self) -> str:
        return f"SingleCandidatePolicy(min_confidence={self.min_confidence})"


class WhitelistPolicy(DecisionPolicy):
    """
    Policy: Aprobar solo intents en whitelist.
    
    Útil para modo restringido o permisos por usuario.
    """
    
    def __init__(self, allowed_intents: List[str]):
        self.allowed_intents = set(allowed_intents)
    
    def apply(self, candidates: List[IntentCandidate]) -> PolicyResult:
        # Filtrar solo candidatos permitidos
        allowed_candidates = [c for c in candidates if c.intent in self.allowed_intents]
        
        if not allowed_candidates:
            rejected = [c.intent for c in candidates]
            return PolicyResult(
                decision=PolicyDecision.REJECT,
                reasoning=f"Ningún candidato en whitelist. Rechazados: {rejected}",
                metadata={
                    "whitelist": list(self.allowed_intents),
                    "rejected": rejected
                }
            )
        
        # Elegir mejor de los permitidos
        best = max(allowed_candidates, key=lambda c: c.confidence)
        
        return PolicyResult(
            decision=PolicyDecision.APPROVE,
            chosen_candidate=best,
            reasoning=f"Intent {best.intent} permitido en whitelist",
            metadata={
                "whitelist": list(self.allowed_intents),
                "filtered_out": len(candidates) - len(allowed_candidates)
            }
        )
    
    def __repr__(self) -> str:
        return f"WhitelistPolicy(allowed={len(self.allowed_intents)} intents)"


class BlacklistPolicy(DecisionPolicy):
    """
    Policy: Rechazar intents en blacklist.
    
    Útil para deshabilitar comandos peligrosos o en mantenimiento.
    """
    
    def __init__(self, forbidden_intents: List[str]):
        self.forbidden_intents = set(forbidden_intents)
    
    def apply(self, candidates: List[IntentCandidate]) -> PolicyResult:
        # Filtrar candidatos no prohibidos
        allowed_candidates = [c for c in candidates if c.intent not in self.forbidden_intents]
        
        if not allowed_candidates:
            return PolicyResult(
                decision=PolicyDecision.REJECT,
                reasoning="Todos los candidatos están en blacklist",
                metadata={
                    "blacklist": list(self.forbidden_intents),
                    "rejected": [c.intent for c in candidates]
                }
            )
        
        # Elegir mejor de los permitidos
        best = max(allowed_candidates, key=lambda c: c.confidence)
        
        filtered = [c.intent for c in candidates if c.intent in self.forbidden_intents]
        
        return PolicyResult(
            decision=PolicyDecision.APPROVE,
            chosen_candidate=best,
            reasoning=f"Intent {best.intent} no está en blacklist",
            metadata={
                "blacklist": list(self.forbidden_intents),
                "filtered_out": filtered
            }
        )
    
    def __repr__(self) -> str:
        return f"BlacklistPolicy(forbidden={len(self.forbidden_intents)} intents)"


class PolicyChain:
    """
    Aplica múltiples policies en secuencia.
    
    Si una policy rechaza/clarifica, se detiene la cadena.
    Si una policy aprueba, continúa a la siguiente.
    
    Uso:
        chain = PolicyChain([
            BlacklistPolicy(["dangerous_command"]),
            ConfidenceThresholdPolicy(threshold=0.7),
            SingleCandidatePolicy()
        ])
        result = chain.apply(candidates)
    """
    
    def __init__(self, policies: List[DecisionPolicy]):
        self.policies = policies
    
    def apply(self, candidates: List[IntentCandidate]) -> PolicyResult:
        """
        Aplica policies en orden hasta que una no-APPROVE.
        """
        current_candidates = candidates
        
        for policy in self.policies:
            result = policy.apply(current_candidates)
            
            # Si policy rechaza o pide clarificación, detener cadena
            if result.decision != PolicyDecision.APPROVE:
                result.metadata["stopped_at_policy"] = str(policy)
                return result
            
            # Si policy aprobó pero filtró candidatos, continuar solo con ese
            if result.chosen_candidate:
                current_candidates = [result.chosen_candidate]
        
        # Todas las policies aprobaron
        if current_candidates:
            best = max(current_candidates, key=lambda c: c.confidence)
            return PolicyResult(
                decision=PolicyDecision.APPROVE,
                chosen_candidate=best,
                reasoning=f"Aprobado por {len(self.policies)} policies",
                metadata={"policies_passed": len(self.policies)}
            )
        
        return PolicyResult(
            decision=PolicyDecision.REJECT,
            reasoning="Sin candidatos después de aplicar policies"
        )
    
    def __repr__(self) -> str:
        return f"PolicyChain({len(self.policies)} policies)"
