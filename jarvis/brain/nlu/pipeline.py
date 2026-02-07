# brain/nlu/pipeline.py
"""
NLU Pipeline v0.0.3.1 - Explicit reasoning with hypothesis generation
Refactored to produce Decision objects with multiple IntentHypothesis alternatives
"""
import traceback
from typing import Dict, List, Optional, Tuple
from brain.nlu.normalizer import Normalizer
from brain.nlu.entities import EntityExtractor
from brain.nlu.parser import IntentParser
from system.core.exceptions import NLUError
from brain.memory.context import ContextManager
from brain.decision import Decision, IntentHypothesis, create_unknown_decision, create_decision_from_hypotheses


class NLUResult:
    """Encapsulates NLU processing result with metadata"""
    
    def __init__(self, intent: str, entities: Dict, raw_text: str, normalized_text: str):
        self.intent = intent
        self.entities = entities
        self.raw_text = raw_text
        self.normalized_text = normalized_text
        self.confidence = 0.0
        self.alternatives = []  # List of (intent, confidence) tuples
        self.trace = []  # Debug trace steps
        self.error = None
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for event emission"""
        return {
            "intent": self.intent,
            "entities": self.entities,
            "raw": self.raw_text,
            "normalized": self.normalized_text,
            "confidence": self.confidence,
            "alternatives": self.alternatives,
            "trace": self.trace if self.trace else None
        }


class NLUPipeline:
    """
    NLU Pipeline with confidence scoring, debug tracing, and context awareness
    """
    
    def __init__(self, skills_registry, debug=False, context_manager=None, runtime_state=None):
        self.norm = Normalizer()
        self.entities = EntityExtractor(skills_registry)
        self.intent = IntentParser(skills_registry)
        self.debug = debug
        self.skills_registry = skills_registry
        self.confidence_threshold = 0.5  # Minimum confidence for intent recognition
        self.context = context_manager or ContextManager()  # Always use context
        self.runtime_state = runtime_state  # NEW: Store decisions here directly

    def _log(self, *msg):
        """Log debug messages if debug mode enabled"""
        if self.debug:
            print("[NLU]", *msg)
    
    def _trace(self, result: NLUResult, step: str, details: str):
        """Add trace step for debugging"""
        trace_entry = {
            "step": step,
            "details": details
        }
        result.trace.append(trace_entry)
        self._log(f"TRACE[{step}]: {details}")
    
    def generate_hypotheses(self, normalized_text: str, entities: Dict[str, any]) -> List[IntentHypothesis]:
        """
        Generate multiple intent hypotheses for the input.
        Each hypothesis explains why a particular intent might match.
        
        Args:
            normalized_text: Cleaned/normalized input
            entities: Extracted entities
            
        Returns:
            List of IntentHypothesis objects, may be empty
        """
        hypotheses = []
        
        # Ask parser for all possible matches with scores
        matches = self.intent.parse_all_matches(normalized_text, entities)
        
        for intent_name, score, patterns in matches:
            # Build explanation
            explanation_parts = []
            
            if patterns:
                pattern_str = patterns[0] if len(patterns) == 1 else f"{len(patterns)} patterns"
                explanation_parts.append(f"matched {pattern_str}")
            
            if entities:
                entity_list = ", ".join(f"{k}={v}" for k, v in list(entities.items())[:2])
                explanation_parts.append(f"with entities: {entity_list}")
            
            explanation = " ".join(explanation_parts) if explanation_parts else "pattern match"
            
            hypothesis = IntentHypothesis(
                intent_name=intent_name,
                score=score,
                matched_patterns=patterns,
                explanation=explanation,
                supporting_entities=entities.copy()
            )
            
            hypotheses.append(hypothesis)
            self._log(f"Hypothesis: {intent_name} (score={score:.2f}) - {explanation}")
        
        return hypotheses
    
    def select_intent(self, hypotheses: List[IntentHypothesis], raw_input: str, 
                     normalized_input: str, entities: Dict[str, any]) -> Decision:
        """
        Select best intent from hypotheses and create Decision object.
        Applies deterministic selection rules.
        
        Args:
            hypotheses: List of IntentHypothesis
            raw_input: Original user text
            normalized_input: Normalized text
            entities: Extracted entities
            
        Returns:
            Decision object with selected intent and reasoning
        """
        decision = create_decision_from_hypotheses(
            raw_input=raw_input,
            normalized_input=normalized_input,
            hypotheses=hypotheses,
            entities=entities,
            confidence_threshold=self.confidence_threshold
        )
        
        self._log(f"Decision: {decision.selected_intent} (confidence={decision.confidence:.2f})")
        self._log(f"Reasoning: {decision.reasoning}")
        
        return decision

    def process(self, text: str, eventbus) -> Decision:
        """
        Process text through NLU pipeline with explicit reasoning (v0.0.3.1).
        Returns Decision object instead of NLUResult.
        
        Args:
            text: Input text to process
            eventbus: Event bus for emitting semantic events
            
        Returns:
            Decision object with intent, hypotheses, and reasoning
        """
        raw = text.strip()
        
        # Emit OBSERVATION_CREATED
        eventbus.emit("cognitive.observation_created", {"text": raw})
        
        if not raw:
            decision = create_unknown_decision(raw, "", "Empty input provided")
            eventbus.emit("cognitive.decision_made", decision.to_dict())
            return decision
        
        try:
            # Step 1: Normalization
            clean = self.norm.run(raw)
            self._log(f"Normalized: '{raw}' → '{clean}'")
            
            # Step 2: Entity Extraction
            try:
                entities = self.entities.extract(clean)
                self._log(f"Entities: {entities}")
            except Exception as e:
                self._log(f"Entity extraction warning: {e}")
                entities = {}
            
            # Emit INTERPRETATION_COMPLETED
            eventbus.emit("cognitive.interpretation_completed", {
                "raw": raw,
                "normalized": clean,
                "entities": entities
            })
            
            # Step 3: Generate Hypotheses
            hypotheses = self.generate_hypotheses(clean, entities)
            self._log(f"Generated {len(hypotheses)} hypotheses")
            
            # Step 4: Select Intent and Create Decision
            decision = self.select_intent(hypotheses, raw, clean, entities)
            
            # Store last decision for event handler
            self._last_decision = decision
            
            # V0.0.3.1: Store decision directly in RuntimeState if available
            if self.runtime_state:
                self.runtime_state.add_decision(decision)
            
            # Step 5: Store in context
            try:
                self.context.add_intent(decision.selected_intent, decision.confidence, decision.entities)
            except Exception as e:
                self._log(f"Context storage warning: {e}")
            
            # Emit DECISION_MADE
            eventbus.emit("cognitive.decision_made", decision.to_dict())
            
            # Backward compatibility: also emit old-style nlu.intent
            eventbus.emit("nlu.intent", decision.to_dict())
            
            return decision
            
        except Exception as e:
            self._log(f"NLU Error: {e}")
            traceback.print_exc()
            
            # Create error decision
            decision = create_unknown_decision(
                raw, 
                clean if 'clean' in locals() else raw,
                f"Processing error: {str(e)}"
            )
            
            eventbus.emit("nlu.error", {
                "error": str(e),
                "text": raw,
                "decision_id": decision.decision_id
            })
            
            eventbus.emit("cognitive.decision_made", decision.to_dict())
            
            return decision
