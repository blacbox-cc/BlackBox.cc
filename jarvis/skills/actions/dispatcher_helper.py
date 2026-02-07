"""
DispatcherHelper: Helpers para dispatcher usando FASE 4 policies.

En lugar de modificar dispatcher.py directamente (alto riesgo), creamos helpers
que demuestran cómo aplicar policies sin romper código existente.

Objetivos:
- Proof-of-concept: mostrar cómo usar DecisionPolicy y ExecutionPolicy
- Sin regresiones: dispatcher.py sigue funcionando
- Gradual: dispatcher.py puede migrar a policies incrementalmente
"""

from typing import List, Dict, Any, Optional
from core.helpers import (
    IntentCandidate, Decision, DecisionType,
    DecisionPolicy, PolicyResult, ConfidenceThresholdPolicy,
    ExecutionPolicy, ExecutionPolicyResult, SafeModePolicy,
    PolicyChain, ExecutionPolicyChain
)


class DispatcherHelper:
    """
    Helper functions para dispatcher usando policies FASE 4.
    
    Provee versiones alternativas de lógica de dispatch que usan
    DecisionPolicy y ExecutionPolicy en lugar de if/else dispersos.
    """
    
    @staticmethod
    def select_intent_with_policy(
        candidates: List[IntentCandidate],
        policy: Optional[DecisionPolicy] = None
    ) -> Decision:
        """
        Selecciona intent usando DecisionPolicy explícito.
        
        Args:
            candidates: Lista de IntentCandidates del NLU
            policy: DecisionPolicy a aplicar (default: ConfidenceThreshold)
        
        Returns:
            Decision con intent elegido o reasoning de rechazo
        """
        if policy is None:
            # Default policy: threshold 0.7, gap 0.15
            policy = ConfidenceThresholdPolicy(threshold=0.7, min_gap=0.15)
        
        # Aplicar policy
        result = policy.apply(candidates)
        
        # Convertir PolicyResult a Decision
        if result.approved:
            return Decision.single_match(
                candidate=result.chosen_candidate,
                reasoning=result.reasoning
            )
        elif result.needs_clarification:
            # Low confidence o ambigüedad
            return Decision.low_confidence(
                candidates=candidates,
                reasoning=result.reasoning
            )
        else:
            # Rechazado
            return Decision.no_match(
                reasoning=result.reasoning
            )
    
    @staticmethod
    def should_execute_with_policy(
        intent: str,
        context: Dict[str, Any],
        policy: Optional[ExecutionPolicy] = None
    ) -> ExecutionPolicyResult:
        """
        Decide si ejecutar intent usando ExecutionPolicy.
        
        Args:
            intent: Intent a ejecutar
            context: Contexto (entities, user, session)
            policy: ExecutionPolicy a aplicar (default: SafeMode)
        
        Returns:
            ExecutionPolicyResult con decisión
        """
        if policy is None:
            # Default policy: SafeMode básico
            policy = SafeModePolicy()
        
        return policy.should_execute(intent, context)
    
    @staticmethod
    def dispatch_with_policies(
        candidates: List[IntentCandidate],
        context: Dict[str, Any],
        decision_policy: Optional[DecisionPolicy] = None,
        execution_policy: Optional[ExecutionPolicy] = None
    ) -> Dict[str, Any]:
        """
        Pipeline completo de dispatch con policies explícitos.
        
        Flujo:
        1. DecisionPolicy selecciona intent
        2. ExecutionPolicy valida si ejecutar
        3. Retorna resultado con reasoning observable
        
        Args:
            candidates: Candidatos del NLU
            context: Contexto de ejecución
            decision_policy: Policy para selección (opcional)
            execution_policy: Policy para ejecución (opcional)
        
        Returns:
            Dict con {intent, should_execute, reasoning, metadata}
        """
        # Paso 1: Seleccionar intent
        decision = DispatcherHelper.select_intent_with_policy(
            candidates=candidates,
            policy=decision_policy
        )
        
        if decision.decision_type == DecisionType.NO_MATCH:
            return {
                "intent": None,
                "should_execute": False,
                "reasoning": decision.reasoning,
                "stage": "decision_policy",
                "metadata": {
                    "decision_type": decision.decision_type.value,
                    "candidates_count": len(candidates)
                }
            }
        
        if decision.decision_type == DecisionType.LOW_CONFIDENCE:
            return {
                "intent": decision.chosen_candidate.intent if decision.chosen_candidate else None,
                "should_execute": False,
                "reasoning": decision.reasoning,
                "stage": "decision_policy",
                "metadata": {
                    "decision_type": decision.decision_type.value,
                    "alternatives": [c.intent for c in decision.all_candidates]
                }
            }
        
        # Paso 2: Validar ejecución
        chosen_intent = decision.chosen_candidate.intent
        execution_result = DispatcherHelper.should_execute_with_policy(
            intent=chosen_intent,
            context=context,
            policy=execution_policy
        )
        
        if execution_result.blocked:
            return {
                "intent": chosen_intent,
                "should_execute": False,
                "reasoning": execution_result.reasoning,
                "stage": "execution_policy",
                "metadata": execution_result.metadata
            }
        
        if execution_result.needs_confirmation:
            return {
                "intent": chosen_intent,
                "should_execute": False,
                "requires_confirmation": True,
                "reasoning": execution_result.reasoning,
                "stage": "execution_policy",
                "metadata": execution_result.metadata
            }
        
        # Todo OK: aprobar ejecución
        return {
            "intent": chosen_intent,
            "should_execute": True,
            "reasoning": f"Aprobado por decision y execution policies",
            "stage": "approved",
            "metadata": {
                "decision_reasoning": decision.reasoning,
                "execution_reasoning": execution_result.reasoning,
                "confidence": decision.chosen_candidate.confidence
            }
        }
    
    @staticmethod
    def create_default_policy_chain() -> PolicyChain:
        """
        Crea chain de DecisionPolicies con configuración default.
        
        Returns:
            PolicyChain con ConfidenceThreshold
        """
        return PolicyChain([
            ConfidenceThresholdPolicy(threshold=0.7, min_gap=0.15)
        ])
    
    @staticmethod
    def create_safe_execution_chain() -> ExecutionPolicyChain:
        """
        Crea chain de ExecutionPolicies para modo seguro.
        
        Returns:
            ExecutionPolicyChain con SafeMode
        """
        return ExecutionPolicyChain([
            SafeModePolicy()
        ])
    
    @staticmethod
    def create_production_execution_chain() -> ExecutionPolicyChain:
        """
        Crea chain de ExecutionPolicies para producción.
        
        Incluye: SafeMode + RateLimit + Confirmation
        
        Returns:
            ExecutionPolicyChain completo
        """
        from core.helpers import RateLimitPolicy, ConfirmationPolicy
        
        return ExecutionPolicyChain([
            SafeModePolicy(),
            RateLimitPolicy(max_per_minute=30),
            ConfirmationPolicy()
        ])
