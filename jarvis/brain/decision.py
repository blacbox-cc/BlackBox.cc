# brain/decision.py
"""
Decision Model - Explicit reasoning layer for JarvisAI v0.0.3.1
Represents a complete decision context with hypothesis generation and selection reasoning.
"""

import uuid
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class IntentHypothesis:
    """
    Represents one possible interpretation of user input.
    Each hypothesis explains why a particular intent might match.
    """
    intent_name: str
    score: float  # 0.0 to 1.0
    matched_patterns: List[str] = field(default_factory=list)
    explanation: str = ""
    supporting_entities: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate score range"""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.score}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "intent_name": self.intent_name,
            "score": self.score,
            "matched_patterns": self.matched_patterns,
            "explanation": self.explanation,
            "supporting_entities": self.supporting_entities
        }


@dataclass
class Decision:
    """
    Central decision object containing complete reasoning context.
    Created for every user input regardless of success or failure.
    Does NOT execute actions - only represents cognitive state.
    """
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    raw_input: str = ""
    normalized_input: str = ""
    intent_candidates: List[IntentHypothesis] = field(default_factory=list)
    selected_intent: Optional[str] = None
    confidence: float = 0.0
    rejected_intents: List[str] = field(default_factory=list)
    reasoning: str = ""
    entities: Dict[str, Any] = field(default_factory=dict)
    execution_allowed: bool = False
    decision_trace: List[Dict[str, str]] = field(default_factory=list)
    
    def add_trace_step(self, step: str, details: str):
        """Add a reasoning step to trace"""
        self.decision_trace.append({
            "step": step,
            "details": details
        })
    
    def get_top_alternatives(self, n: int = 3) -> List[IntentHypothesis]:
        """Get top N alternative hypotheses (excluding selected)"""
        alternatives = [h for h in self.intent_candidates 
                       if h.intent_name != self.selected_intent]
        return sorted(alternatives, key=lambda h: h.score, reverse=True)[:n]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for backward compatibility.
        Maintains same structure as v0.0.3 NLU results.
        """
        return {
            "intent": self.selected_intent or "unknown",
            "entities": self.entities,
            "raw": self.raw_input,
            "normalized": self.normalized_input,
            "confidence": self.confidence,
            "alternatives": [
                (h.intent_name, h.score) 
                for h in self.get_top_alternatives()
            ],
            "trace": self.decision_trace if self.decision_trace else None,
            # v0.0.3.1 additions
            "decision_id": self.decision_id,
            "reasoning": self.reasoning,
            "execution_allowed": self.execution_allowed
        }
    
    def to_full_dict(self) -> Dict[str, Any]:
        """Convert to complete dictionary including all hypotheses"""
        return {
            "decision_id": self.decision_id,
            "decision_timestamp": self.decision_timestamp,
            "raw_input": self.raw_input,
            "normalized_input": self.normalized_input,
            "intent_candidates": [h.to_dict() for h in self.intent_candidates],
            "selected_intent": self.selected_intent,
            "confidence": self.confidence,
            "rejected_intents": self.rejected_intents,
            "reasoning": self.reasoning,
            "entities": self.entities,
            "execution_allowed": self.execution_allowed,
            "decision_trace": self.decision_trace
        }
    
    def __getitem__(self, key):
        """
        Allow dict-like access for backward compatibility.
        Makes Decision objects compatible with v0.0.3 code expecting dicts.
        """
        compat_dict = self.to_dict()
        return compat_dict[key]
    
    def get(self, key, default=None):
        """Dict-like get method for backward compatibility"""
        try:
            return self[key]
        except KeyError:
            return default


def create_unknown_decision(raw_input: str, normalized_input: str, reason: str = "No patterns matched") -> Decision:
    """
    Factory function for creating unknown intent decisions.
    Used when NLU cannot match any pattern.
    """
    decision = Decision(
        raw_input=raw_input,
        normalized_input=normalized_input,
        selected_intent="unknown",
        confidence=0.0,
        reasoning=reason,
        execution_allowed=False
    )
    decision.add_trace_step("unknown", reason)
    return decision


def create_decision_from_hypotheses(
    raw_input: str,
    normalized_input: str,
    hypotheses: List[IntentHypothesis],
    entities: Dict[str, Any],
    confidence_threshold: float = 0.5
) -> Decision:
    """
    Factory function for creating decisions from hypothesis list.
    Applies deterministic selection algorithm.
    """
    decision = Decision(
        raw_input=raw_input,
        normalized_input=normalized_input,
        intent_candidates=hypotheses,
        entities=entities
    )
    
    if not hypotheses:
        decision.selected_intent = "unknown"
        decision.confidence = 0.0
        decision.reasoning = "No patterns matched input"
        decision.execution_allowed = False
        decision.add_trace_step("selection", "No hypotheses generated")
        return decision
    
    # Select hypothesis with highest score
    selected = max(hypotheses, key=lambda h: h.score)
    decision.selected_intent = selected.intent_name
    
    # CONFIDENCE HONESTO: Reducir si solo hay 1 hipótesis
    if len(hypotheses) == 1:
        # Solo 1 match = no comparación = bajo confidence
        decision.confidence = min(0.6, selected.score)
        confidence_note = " (única hipótesis, sin comparación)"
    else:
        # Múltiples hipótesis = comparación real
        decision.confidence = selected.score
        confidence_note = f" ({len(hypotheses)} alternativas consideradas)"
    
    # Build reasoning text
    reasoning_parts = [
        f"Selected {selected.intent_name} (score={decision.confidence:.2f}{confidence_note})"
    ]
    
    if selected.explanation:
        reasoning_parts.append(f"because {selected.explanation}")
    
    if selected.matched_patterns:
        pattern_str = ", ".join(selected.matched_patterns[:2])
        reasoning_parts.append(f"matched patterns: {pattern_str}")
    
    if entities:
        entity_str = ", ".join(f"{k}={v}" for k, v in entities.items())
        reasoning_parts.append(f"with entities: {entity_str}")
    
    decision.reasoning = " ".join(reasoning_parts)
    
    # Check confidence threshold
    if decision.confidence < confidence_threshold:
        decision.reasoning += f"; low confidence (< {confidence_threshold}), requesting confirmation"
        decision.execution_allowed = False
    else:
        decision.execution_allowed = True
    
    # Record rejected intents
    decision.rejected_intents = [
        h.intent_name for h in hypotheses 
        if h.intent_name != selected.intent_name
    ]
    
    # Add trace
    decision.add_trace_step(
        "selection",
        f"{selected.intent_name} chosen with score {decision.confidence:.2f}"
    )
    
    if decision.rejected_intents:
        decision.add_trace_step(
            "rejected",
            f"Alternatives: {', '.join(decision.rejected_intents[:3])}"
        )
    
    return decision
