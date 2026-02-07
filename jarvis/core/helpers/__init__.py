# core/helpers/__init__.py
"""
Core Helpers - Refactor FASE 1, 2, 3, 4, 5 y 6
Helpers fundamentales para contratos explícitos y operaciones seguras.
"""

from .result import Result, Outcome, Success, Failure
from .guard import Guard, Precondition
from .error_factory import ErrorFactory, ErrorContext, ErrorType
from .tracer import Tracer, TraceEntry
from .skill_context import SkillContext
from .decision import Decision, IntentCandidate, DecisionType
from .confidence import ConfidenceHelper, ConfidenceScore, ConfidenceLevel
from .match_result import MatchResult
from .decision_policy import (
    DecisionPolicy, PolicyResult, PolicyDecision,
    ConfidenceThresholdPolicy, SingleCandidatePolicy,
    WhitelistPolicy, BlacklistPolicy, PolicyChain
)
from .execution_policy import (
    ExecutionPolicy, ExecutionPolicyResult, ExecutionDecision,
    SafeModePolicy, RateLimitPolicy, ConfirmationPolicy,
    PermissionPolicy, ExecutionPolicyChain
)
from .skill_executor import SkillExecutor, ExecutionResult, ExecutionStatus
from .reflection import (
    ComponentStatus, ComponentHealth, SystemHealth,
    DecisionExplainer, StateSnapshot
)

__all__ = [
    # Result/Outcome (FASE 1)
    "Result",
    "Outcome", 
    "Success",
    "Failure",
    # Guard/Preconditions (FASE 1)
    "Guard",
    "Precondition",
    # Error Factory (FASE 1)
    "ErrorFactory",
    "ErrorContext",
    "ErrorType",
    # Tracer (FASE 1)
    "Tracer",
    "TraceEntry",
    # Contratos (FASE 2)
    "SkillContext",
    "Decision",
    "IntentCandidate",
    "DecisionType",
    # NLU Helpers (FASE 3)
    "ConfidenceHelper",
    "ConfidenceScore",
    "ConfidenceLevel",
    "MatchResult",
    # Decision Policies (FASE 4)
    "DecisionPolicy",
    "PolicyResult",
    "PolicyDecision",
    "ConfidenceThresholdPolicy",
    "SingleCandidatePolicy",
    "WhitelistPolicy",
    "BlacklistPolicy",
    "PolicyChain",
    # Execution Policies (FASE 4)
    "ExecutionPolicy",
    "ExecutionPolicyResult",
    "ExecutionDecision",
    "SafeModePolicy",
    "RateLimitPolicy",
    "ConfirmationPolicy",
    "PermissionPolicy",
    "ExecutionPolicyChain",
    # Execution Wrapper (FASE 5)
    "SkillExecutor",
    "ExecutionResult",
    "ExecutionStatus",
    # Reflection Mínima (FASE 6)
    "ComponentStatus",
    "ComponentHealth",
    "SystemHealth",
    "DecisionExplainer",
    "StateSnapshot",
]
